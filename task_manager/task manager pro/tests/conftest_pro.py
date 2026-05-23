"""Pytest configuration and fixtures for Task Manager Pro."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database_pro import Base, get_db
from app.main_pro import app


# Database fixtures
@pytest.fixture
def db_engine():
    """Create in-memory SQLite database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine, expire_on_commit=False)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def client(db_session):
    """Create FastAPI test client."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# Test data fixtures
@pytest.fixture
def test_user_data():
    """Sample user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "role": "user",
    }


@pytest.fixture
def test_project_data():
    """Sample project data."""
    return {
        "title": "Test Project",
        "description": "A test project",
    }


@pytest.fixture
def test_task_data():
    """Sample task data."""
    return {
        "title": "Test Task",
        "description": "A test task",
        "status": "todo",
        "priority": "medium",
    }


@pytest.fixture
def test_comment_data():
    """Sample comment data."""
    return {
        "content": "This is a test comment",
    }


@pytest.fixture
def test_tag_data():
    """Sample tag data."""
    return {
        "name": "important",
        "color": "#FF0000",
    }
