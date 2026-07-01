"""Security utilities for authentication and request hardening."""

import re
import time
import threading

from fastapi import Request, Depends, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings

RATE_LIMIT_STORE: dict[str, tuple[float, int]] = {}
RATE_LIMIT_LOCK = threading.Lock()


def clear_rate_limit_store() -> None:
    """Reset in-memory rate limit state (for tests)."""
    with RATE_LIMIT_LOCK:
        RATE_LIMIT_STORE.clear()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply standard HTTP security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if not settings.enable_security_headers:
            return response

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


def validate_password_policy(password: str) -> None:
    """Validate password strength according to configured security policy."""
    if len(password) < settings.password_min_length:
        raise ValueError(f"Password must be at least {settings.password_min_length} characters long")

    if settings.password_require_uppercase and not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if settings.password_require_lowercase and not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if settings.password_require_digit and not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    if settings.password_require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")


def get_client_ip(request: Request) -> str:
    """Resolve the client IP address from request headers."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def rate_limit_request(request: Request, endpoint: str) -> None:
    """Rate-limit authentication endpoints by client IP and endpoint."""
    key = f"{get_client_ip(request)}:{endpoint}"
    now = time.time()
    window = settings.auth_rate_limit_window_seconds
    limit = settings.auth_rate_limit_max_attempts

    with RATE_LIMIT_LOCK:
        entry = RATE_LIMIT_STORE.get(key)
        if entry is None or entry[0] + window < now:
            RATE_LIMIT_STORE[key] = (now, 1)
            return

        started_at, count = entry
        if count >= limit:
            reset = started_at + window
            retry_after = int(max(0, reset - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        RATE_LIMIT_STORE[key] = (started_at, count + 1)


def auth_rate_limit(endpoint: str):
    """Dependency factory for auth endpoint rate limiting."""
    async def dependency(request: Request):
        rate_limit_request(request, endpoint)
    return Depends(dependency)
