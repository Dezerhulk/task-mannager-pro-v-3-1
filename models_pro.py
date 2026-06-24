"""SQLAlchemy ORM models for Task Manager Pro."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, 
    JSON, String, Text, UniqueConstraint, Index, Table
)
from sqlalchemy.orm import relationship

from .database_pro import Base


class UserRoleEnum(str, Enum):
    """User roles for access control."""
    admin = "admin"
    manager = "manager"
    user = "user"


class TaskStatusEnum(str, Enum):
    """Task status values."""
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"
    archived = "archived"


class TaskPriorityEnum(str, Enum):
    """Task priority levels."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ProjectRoleEnum(str, Enum):
    """Roles within a project."""
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


# Association tables for many-to-many relationships
project_members = Table(
    'project_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_project_members', 'user_id', 'project_id'),
)

task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_task_tags', 'task_id', 'tag_id'),
)


class User(Base):
    """User model."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRoleEnum), default=UserRoleEnum.user, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    created_tasks = relationship("Task", back_populates="creator", foreign_keys="Task.creator_id")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    owned_projects = relationship("Project", back_populates="owner")
    comments = relationship("Comment", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    projects = relationship("Project", secondary=project_members, back_populates="members")
    project_memberships = relationship(
        "ProjectMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index('idx_users_email_active', 'email', 'is_active'),
        Index('idx_users_role', 'role'),
    )


class Project(Base):
    """Project model."""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owned_projects")
    members = relationship("User", secondary=project_members, back_populates="projects")
    memberships = relationship(
        "ProjectMembership",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project")
    tags = relationship("Tag", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_projects_owner_deleted', 'owner_id', 'is_deleted'),
    )


class Tag(Base):
    """Tag model for categorizing tasks."""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    color = Column(String(7), nullable=True)  # Hex color #RRGGBB
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tags")
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")

    __table_args__ = (
        UniqueConstraint('project_id', 'name', name='uq_tags_project_name'),
        Index('idx_tags_project_name', 'project_id', 'name'),
    )


class Task(Base):
    """Task model."""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    assignee_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(TaskStatusEnum), default=TaskStatusEnum.todo, nullable=False)
    priority = Column(SQLEnum(TaskPriorityEnum), default=TaskPriorityEnum.medium, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    creator = relationship("User", back_populates="created_tasks", foreign_keys=[creator_id])
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    audit_logs = relationship("AuditLog", back_populates="task")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_tasks_project_status', 'project_id', 'status'),
        Index('idx_tasks_project_deleted', 'project_id', 'is_deleted'),
        Index('idx_tasks_assignee_status', 'assignee_id', 'status'),
        Index('idx_tasks_priority_deadline', 'priority', 'deadline'),
    )


class Subtask(Base):
    """Subtasks attached to a task for workflow tracking."""
    __tablename__ = 'subtasks'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    done = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    task = relationship("Task", back_populates="subtasks")


class TaskAttachment(Base):
    """Attachments for a task."""
    __tablename__ = 'task_attachments'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    task = relationship("Task", back_populates="attachments")


class TaskHistory(Base):
    """Immutable task history records for workflow auditing."""
    __tablename__ = 'task_history'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    event_type = Column(String(50), nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    task = relationship("Task", back_populates="history")
    actor = relationship("User")


class Comment(Base):
    """Comment model for task discussions."""
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")
    audit_logs = relationship("AuditLog", back_populates="comment")

    __table_args__ = (
        Index('idx_comments_task_user', 'task_id', 'user_id'),
        Index('idx_comments_created_at', 'created_at'),
    )


class AuditLog(Base):
    """Audit log model for tracking changes."""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='SET NULL'), nullable=True)
    entity_type = Column(String(50), nullable=False)  # 'user', 'project', 'task', 'comment'
    action = Column(String(20), nullable=False)  # 'create', 'update', 'delete'
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    project = relationship("Project", back_populates="audit_logs")
    task = relationship("Task", back_populates="audit_logs")
    comment = relationship("Comment", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_logs_entity', 'entity_type', 'created_at'),
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
    )


class RefreshToken(Base):
    """Refresh token model for rotating and revoking refresh tokens."""
    __tablename__ = 'refresh_tokens'

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index('idx_refresh_tokens_user', 'user_id'),
        Index('idx_refresh_tokens_jti', 'jti'),
    )


class ProjectMembership(Base):
    """Project membership with a per-project role."""
    __tablename__ = 'project_memberships'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(SQLEnum(ProjectRoleEnum), nullable=False, default=ProjectRoleEnum.member)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', name='uq_project_memberships_user_project'),
        Index('idx_project_memberships_project_role', 'project_id', 'role'),
    )

    user = relationship("User", back_populates="project_memberships")
    project = relationship("Project", back_populates="memberships")


class Notification(Base):
    """User-facing notification records."""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(50), default='in_app', nullable=False, index=True)
    delivery_status = Column(String(30), default='sent', nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    delivery_metadata = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="notifications")
    project = relationship("Project")
    task = relationship("Task")

    __table_args__ = (
        Index('idx_notifications_user_read', 'user_id', 'is_read'),
    )
