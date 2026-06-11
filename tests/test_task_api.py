import importlib
import sys
import time

import pytest


def get_token(client, username="alice", password="Alice12345!"):
    # Try to register first (will fail if user exists, which is fine)
    client.post("/api/auth/register", json={"username": username, "password": password})

    # Now login
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert token
    return token


def test_token_creation(client):
    token = get_token(client)
    assert token is not None


def test_legacy_auth_routes_removed(client):
    response = client.post(
        "/register",
        json={"username": "legacy", "password": "LegacyPass123!"},
    )
    assert response.status_code == 404

    response = client.post(
        "/login",
        json={"username": "legacy", "password": "LegacyPass123!"},
    )
    assert response.status_code == 404


def test_missing_secret_key_raises(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "change-me-in-production")

    for module_name in ["config"]:
        if module_name in sys.modules:
            del sys.modules[module_name]

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        import config


def test_create_task_and_get_status(client):
    token = get_token(client)
    response = client.post(
        "/tasks",
        json={"data": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    for _ in range(10):
        response = client.get(
            f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == "done":
            break
        time.sleep(0.5)

    assert payload["id"] == task_id
    assert payload["status"] == "done"
    assert payload["result"] == "HELLO"


def test_forbidden_task_access(client):
    alice_token = get_token(client, username="alice", password="Alice12345!")
    response = client.post(
        "/tasks",
        json={"data": "secret"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    bob_token = get_token(client, username="bob", password="BobPass123!")
    response = client.get(
        f"/tasks/{task_id}", headers={"Authorization": f"Bearer {bob_token}"}
    )
    assert response.status_code == 403


def test_create_and_list_project_tasks(client):
    token = get_token(client, username="alice", password="Alice12345!")

    project_response = client.post(
        "/api/projects",
        json={"title": "Alpha Board", "description": "Project task smoke test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    task_response = client.post(
        f"/api/projects/{project_id}/tasks",
        json={"title": "Write release notes", "description": "Prepare summary for release", "assignee": "alice"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert task_response.status_code == 200
    task_id = task_response.json()["task_id"]

    list_response = client.get(
        f"/api/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200

    tasks = {item["id"]: item for item in list_response.json()}
    assert task_id in tasks
    assert tasks[task_id]["title"] == "Write release notes"
    assert tasks[task_id]["description"] == "Prepare summary for release"
    assert tasks[task_id]["project_id"] == project_id


def test_rate_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT", "1")

    for module_name in ["config", "storage", "task_api"]:
        if module_name in sys.modules:
            del sys.modules[module_name]

    import config  # noqa: F401
    import storage  # noqa: F401
    import task_api  # noqa: F401
    importlib.reload(config)
    importlib.reload(storage)
    importlib.reload(task_api)

    from fastapi.testclient import TestClient

    with TestClient(task_api.app) as client:
        token = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post("/tasks", json={"data": "one"}, headers=headers)
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        response = client.get(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 429
