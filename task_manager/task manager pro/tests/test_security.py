"""Tests for security hardening features."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main_pro import app
from app.database_pro import Base, get_db
from app.models_pro import User, UserRoleEnum
from app.security import clear_rate_limit_store

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base.metadata.create_all(bind=engine)

STRONG_PASSWORD = "SecurePass1!"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    clear_rate_limit_store()
    yield


def register_user(username: str, email: str, password: str = STRONG_PASSWORD):
    return client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )


def login_user(email: str, password: str = STRONG_PASSWORD):
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )


def promote_to_admin(email: str):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    user.role = UserRoleEnum.admin
    db.commit()
    db.close()


def test_password_policy_rejects_weak_password():
    response = register_user("weakuser", "weak@example.com", password="short")
    assert response.status_code == 422


def test_security_headers_on_responses():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in response.headers


def test_rate_limit_on_login():
    register_user("ratelimit", "rate@example.com")
    for _ in range(5):
        response = login_user("rate@example.com")
        assert response.status_code in (200, 401)

    blocked = login_user("rate@example.com", password="WrongPass1!")
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_logout_all_revokes_refresh_tokens():
    register_user("logoutall", "logoutall@example.com")
    login_response = login_user("logoutall@example.com")
    tokens = login_response.json()

    logout_all = client.post(
        "/api/auth/logout/all",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_all.status_code == 200
    assert logout_all.json()["revoked"] >= 1

    refresh_response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 401


def test_admin_can_revoke_all_refresh_tokens_globally():
    register_user("usera", "usera@example.com")
    register_user("userb", "userb@example.com")
    tokens_a = login_user("usera@example.com").json()
    tokens_b = login_user("userb@example.com").json()

    promote_to_admin("usera@example.com")
    admin_tokens = tokens_a

    revoke_response = client.post(
        "/api/auth/admin/revoke-refresh-tokens",
        json={},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["revoked"] >= 2

    refresh_a = client.post("/api/auth/refresh", json={"refresh_token": tokens_a["refresh_token"]})
    refresh_b = client.post("/api/auth/refresh", json={"refresh_token": tokens_b["refresh_token"]})
    assert refresh_a.status_code == 401
    assert refresh_b.status_code == 401


def test_failed_login_creates_audit_log():
    register_user("audituser", "audit@example.com")
    response = login_user("audit@example.com", password="WrongPass1!")
    assert response.status_code == 401

    db = TestingSessionLocal()
    from app.models_pro import AuditLog

    log = (
        db.query(AuditLog)
        .filter(AuditLog.action == "failed_login")
        .order_by(AuditLog.id.desc())
        .first()
    )
    db.close()
    assert log is not None
    assert log.new_values.get("email") == "audit@example.com"
