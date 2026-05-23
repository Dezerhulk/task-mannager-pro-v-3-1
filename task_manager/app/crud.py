 and create all new files wit out replesmen+"""CRUD operations for Task Manager."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func, join
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, Project, Task, Comment


class NotFoundError(Exception):
    """Exception raised when a resource is not found."""
    pass


# User operations
def create_user(db: Session, username: str, email: str) -> User:
    """Create a new user."""
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


# Project operations
def create_project(db: Session, title: str, description: Optional[str] = None) -> Project:
    """Create a new project."""
    project = Project(title=title, description=description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """Get project by ID."""
    return db.query(Project).filter(Project.id == project_id).first()


# Task operations
def create_task(
    db: Session,
    title: str,
    description: Optional[str],
    user_id: int,
    project_id: int
) -> Task:
    """Create a new task."""
    # Check if user exists
    user = get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError(f"User with id {user_id} not found")
    
    # Check if project exists
    project = get_project_by_id(db, project_id)
    if not project:
        raise NotFoundError(f"Project with id {project_id} not found")
    
    task = Task(
        title=title,
        description=description,
        user_id=user_id,
        project_id=project_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
    """Get task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def change_task_status(db: Session, task_id: int, status: str) -> Task:
    """Change task status."""
    task = get_task_by_id(db, task_id)
    if not task:
        raise NotFoundError(f"Task with id {task_id} not found")
    
    task.status = status.value if hasattr(status, 'value') else status
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def get_user_tasks(db: Session, user_id: int) -> List[Task]:
    """Get all tasks for a user."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError(f"User with id {user_id} not found")
    
    return db.query(Task).filter(Task.user_id == user_id).all()


def get_project_tasks(db: Session, project_id: int) -> List[Task]:
    """Get all tasks for a project."""
    project = get_project_by_id(db, project_id)
    if not project:
        raise NotFoundError(f"Project with id {project_id} not found")
    
    return db.query(Task).filter(Task.project_id == project_id).all()


def get_tasks_count_by_status(db: Session) -> dict:
    """Get count of tasks grouped by status using func.count."""
    results = (
        db.query(Task.status, func.count(Task.id))
        .group_by(Task.status)
        .all()
    )
    return {status: count for status, count in results}


# Comment operations
def add_comment(db: Session, user_id: int, task_id: int, text: str) -> Comment:
    """Add a comment to a task."""
    # Check if user exists
    user = get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError(f"User with id {user_id} not found")
    
    # Check if task exists
    task = get_task_by_id(db, task_id)
    if not task:
        raise NotFoundError(f"Task with id {task_id} not found")
    
    comment = Comment(user_id=user_id, task_id=task_id, text=text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_task_comments(db: Session, task_id: int) -> List[Comment]:
    """Get all comments for a task."""
    task = get_task_by_id(db, task_id)
    if not task:
        raise NotFoundError(f"Task with id {task_id} not found")
    
    return db.query(Comment).filter(Comment.task_id == task_id).all()


def get_last_user_comments(db: Session, user_id: int, limit: int = 5) -> List[Comment]:
    """Get last N comments for a user using join."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError(f"User with id {user_id} not found")
    
    return (
        db.query(Comment)
        .join(User, Comment.user_id == User.id)
        .filter(User.id == user_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .all()
    )