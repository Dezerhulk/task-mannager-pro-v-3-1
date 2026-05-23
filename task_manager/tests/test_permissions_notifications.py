import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "task manager pro"))

from app.crud_pro import create_notification, get_notifications, mark_notification_read
from app.database_pro import Base, SessionLocal, engine
from app.models_pro import Project, ProjectMembership, ProjectRoleEnum, User
from app.permissions import has_project_permission


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_user(db, username, email, role="user"):
    user = User(
        username=username,
        email=email,
        hashed_password="hashed-password",
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def test_project_permissions_by_role(db_session):
    owner = _create_user(db_session, "owner", "owner@example.com", role="admin")
    admin = _create_user(db_session, "admin", "admin@example.com", role="user")
    member = _create_user(db_session, "member", "member@example.com", role="user")
    viewer = _create_user(db_session, "viewer", "viewer@example.com", role="user")

    project = Project(title="Roadmap", description="", owner_id=owner.id)
    db_session.add(project)
    db_session.flush()

    db_session.add_all(
        [
            ProjectMembership(project_id=project.id, user_id=owner.id, role=ProjectRoleEnum.owner),
            ProjectMembership(project_id=project.id, user_id=admin.id, role=ProjectRoleEnum.admin),
            ProjectMembership(project_id=project.id, user_id=member.id, role=ProjectRoleEnum.member),
            ProjectMembership(project_id=project.id, user_id=viewer.id, role=ProjectRoleEnum.viewer),
        ]
    )
    db_session.commit()

    assert has_project_permission(db_session, project.id, owner.id, "project:read") is True
    assert has_project_permission(db_session, project.id, owner.id, "project:update") is True
    assert has_project_permission(db_session, project.id, admin.id, "project:update") is True
    assert has_project_permission(db_session, project.id, member.id, "project:update") is False
    assert has_project_permission(db_session, project.id, viewer.id, "project:update") is False


def test_notification_flow(db_session):
    user = _create_user(db_session, "notify", "notify@example.com", role="user")

    notification = create_notification(
        db_session,
        user_id=user.id,
        notification_type="task_assigned",
        title="Task assigned",
        message="You were assigned to a task",
    )

    notifications = get_notifications(db_session, user.id)

    assert notification.id is not None
    assert len(notifications) == 1
    assert notifications[0].is_read is False

    marked = mark_notification_read(db_session, notification.id, user.id)
    assert marked is True
    assert get_notifications(db_session, user.id)[0].is_read is True
