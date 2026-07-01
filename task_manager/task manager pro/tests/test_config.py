"""Tests for application configuration validation."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_secret_key_rejected_in_development_without_secret(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, environment="development", secret_key="")


def test_secret_key_rejected_without_explicit_development_mode(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, secret_key="")


def test_secret_key_rejected_in_production(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            environment="production",
            secret_key="dev-secret-key-change-me",
        )


def test_secret_key_rejected_outside_development(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, environment="staging", secret_key="")


def test_cors_wildcard_allowed_in_development(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SECRET_KEY", "dev-test-secret-key-1234567890")
    settings = Settings(_env_file=None, cors_origins="*")
    assert "*" in settings.cors_origins_list


def test_cors_wildcard_rejected_in_staging(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("SECRET_KEY", "a" * 64)
    with pytest.raises(ValidationError, match="CORS"):
        Settings(_env_file=None, cors_origins="*")


def test_cors_wildcard_rejected_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "b" * 64)
    with pytest.raises(ValidationError, match="CORS"):
        Settings(_env_file=None, cors_origins="*")
