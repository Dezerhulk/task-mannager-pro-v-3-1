"""Authorization and permission checking utilities."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models_pro import Project, ProjectMembership, ProjectRoleEnum, Task, User, UserRoleEnum


class PermissionError(HTTPException):
    """Custom permission error."""

    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _get_project_role(db: Session, project_id: int, user_id: int) -> ProjectRoleEnum | None:
    """Return the role for a user on a project, if any."""
    membership = (
        db.query(ProjectMembership)
        .filter(ProjectMembership.project_id == project_id, ProjectMembership.user_id == user_id)
        .first()
    )
    return membership.role if membership else None


def _permission_allowed_for_role(role: ProjectRoleEnum | None, permission: str) -> bool:
    """Map project role to permission grants."""
    if role is None:
        return False

    if permission == "project:read":
        return role in {ProjectRoleEnum.owner, ProjectRoleEnum.admin, ProjectRoleEnum.member, ProjectRoleEnum.viewer}

    if permission == "project:update":
        return role in {ProjectRoleEnum.owner, ProjectRoleEnum.admin}

    if permission == "task:assign":
        return role in {ProjectRoleEnum.owner, ProjectRoleEnum.admin}

    if permission == "task:delete":
        return role in {ProjectRoleEnum.owner, ProjectRoleEnum.admin}

    return False


def has_project_permission(db: Session, project_id: int, user_id: int, permission: str) -> bool:
    """Return whether a user is allowed to perform a project-scoped permission."""
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
    if not project:
        return False

    user = db.query(User).filter(User.id == user_id).first()
    if user and user.role == UserRoleEnum.admin:
        return True

    if project.owner_id == user_id:
        return True

    role = _get_project_role(db, project_id, user_id)
    return _permission_allowed_for_role(role, permission)


async def check_user_exists(db: Session, user_id: int) -> User:
    """Check if user exists, raise 404 if not."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return user


async def check_project_access(
    db: Session,
    project_id: int,
    user_id: int,
    require_owner: bool = False,
    permission: str = "project:read",
) -> Project:
    """Check access to a project and optionally enforce a permission."""
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")

    if require_owner and project.owner_id != user_id:
        raise PermissionError("Only project owner can perform this action")

    if has_project_permission(db, project_id, user_id, permission):
        return project

    raise PermissionError("You don't have access to this project")


async def check_task_access(
    db: Session,
    task_id: int,
    user_id: int,
    permission: str = "task:read",
) -> Task:
    """Check access to a task and optionally enforce a task permission."""
    task = db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

    user = db.query(User).filter(User.id == user_id).first()
    if user and user.role == UserRoleEnum.admin:
        return task

    if permission == "task:read":
        if task.creator_id == user_id or task.assignee_id == user_id:
            return task

    if has_project_permission(db, task.project_id, user_id, permission):
        return task

    raise PermissionError("You don't have access to this task")


async def require_role(user: User, required_role: UserRoleEnum) -> None:
    """Check if user has required role."""
    if user.role not in [UserRoleEnum.admin, required_role]:
        raise PermissionError(f"This action requires {required_role.value} role")


async def require_admin(user: User) -> None:
    """Check if user is admin."""
    if user.role != UserRoleEnum.admin:
        raise PermissionError("Admin access required")
