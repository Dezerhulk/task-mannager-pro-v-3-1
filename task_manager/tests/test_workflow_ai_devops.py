import os
import sys

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "task manager pro"))

from app.crud_pro import create_notification
from app.database_pro import Base, get_db
from app.main_pro import app
from app.models_pro import User


def make_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), engine


def register_and_login(client, username, email, password):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201

    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_project_workflow_and_ai_endpoints():
    client, _ = make_client()
    token = register_and_login(client, "workflow_user", "workflow@example.com", "StrongPass123!")

    response = client.post(
        "/api/projects",
        json={"title": "Workflow Project", "description": "Backlog"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    project_id = response.json()["id"]

    response = client.post(
        f"/api/projects/{project_id}/tags",
        json={"name": "backend", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    label_id = response.json()["id"]

    response = client.post(
        "/api/tasks",
        json={
            "project_id": project_id,
            "title": "Implement API",
            "description": "Add workflow endpoints",
            "status": "todo",
            "priority": "high",
            "tag_ids": [label_id],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    task_id = response.json()["id"]

    response = client.post(
        f"/api/tasks/{task_id}/subtasks",
        json={"title": "Draft schema", "done": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Draft schema"

    response = client.put(
        f"/api/tasks/{task_id}",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    response = client.get(
        f"/api/tasks/kanban?project_id={project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["todo"] == []
    assert payload["in_progress"][0]["id"] == task_id

    response = client.get(
        f"/api/tasks/{task_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1

    response = client.post(
        f"/api/ai/summarize-project/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["project_id"] == project_id

    response = client.post(
        "/api/ai/create-tasks",
        json={"project_id": project_id, "text": "- Ship release notes\n- Review QA checklist"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["tasks"]) >= 2


def test_notification_retry_support():
    client, engine = make_client()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    db = SessionLocal()
    try:
        user = User(
            username="notify_user",
            email="notify@example.com",
            hashed_password="hashed-password",
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        notification = create_notification(
            db,
            user_id=user.id,
            notification_type="task_assigned",
            title="Task assigned",
            message="You were assigned",
            channel="webhook",
            delivery_status="failed",
            error_message="missing endpoint",
        )

        response = client.patch(
            f"/api/notifications/{notification.id}/retry",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
    finally:
        db.close()
