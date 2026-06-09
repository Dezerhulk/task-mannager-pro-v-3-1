"""Configuration management using Pydantic settings."""

import json
from datetime import timedelta
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./task_manager.db"
    sql_echo: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"

    # Security
    secret_key: str = Field("your-secret-key-change-in-production", validation_alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    auth_rate_limit_window_seconds: int = 300
    auth_rate_limit_max_attempts: int = 5
    password_min_length: int = 10
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    enable_security_headers: bool = True
    notification_webhook_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_secret_key(self):
        if self.is_production and self.secret_key == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set and cannot use the default placeholder in production")
        return self

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allow_headers: str = "Authorization,Content-Type,Accept,Origin,X-Requested-With"

    @property
    def cors_origins_list(self) -> list[str]:
        return self._parse_csv_list(self.cors_origins)

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return self._parse_csv_list(self.cors_allow_methods)

    @property
    def cors_allow_headers_list(self) -> list[str]:
        return self._parse_csv_list(self.cors_allow_headers)

    @staticmethod
    def _parse_csv_list(value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        text = value.strip() if isinstance(value, str) else ""
        if not text:
            return []
        if text.startswith("["):
            return json.loads(text)
        return [item.strip() for item in text.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_cors(self):
        if "*" in self.cors_origins_list:
            raise ValueError("CORS origins must not contain '*' in production. Configure explicit origins instead.")
        return self

    # Logging
    log_level: str = "INFO"

    @property
    def access_token_expire(self) -> timedelta:
        """Return access token expiration time."""
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def refresh_token_expire(self) -> timedelta:
        """Return refresh token expiration time."""
        return timedelta(days=self.refresh_token_expire_days)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
