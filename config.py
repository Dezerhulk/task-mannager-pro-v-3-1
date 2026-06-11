import os

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
PLACEHOLDER_SECRET_VALUES = {
    "",
    "replace-me-with-a-long-random-secret",
    "change-me-in-production",
    "change_me_in_production",
    "your-secret-key-change-in-production",
    "dev-secret-change-me-please-123456",
}
if not SECRET_KEY or SECRET_KEY.lower() in {value.lower() for value in PLACEHOLDER_SECRET_VALUES}:
    raise RuntimeError("SECRET_KEY must be set to a non-placeholder value in .env or environment")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
RATE_LIMIT_STR = os.getenv("RATE_LIMIT")
if not RATE_LIMIT_STR:
    raise RuntimeError("RATE_LIMIT must be set in .env or environment")
RATE_LIMIT = int(RATE_LIMIT_STR)
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_BACKEND = os.getenv("RATE_LIMIT_BACKEND", "memory").lower()
REDIS_URL = os.getenv("REDIS_URL")
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "3600"))
REFRESH_TOKEN_EXPIRE_SECONDS = int(os.getenv("REFRESH_TOKEN_EXPIRE_SECONDS", "1209600"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", "sqlite").lower()
QUEUE_DB_PATH = os.getenv("QUEUE_DB_PATH", "queue.db")
DEFAULT_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
CORS_ORIGINS = _split_csv(os.getenv("CORS_ORIGINS", ",".join(DEFAULT_CORS_ORIGINS)))
if "*" in CORS_ORIGINS:
    raise ValueError("CORS_ORIGINS must not contain '*' in production. Configure explicit origins instead.")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() in {"1", "true", "yes", "on"}
CORS_ALLOW_METHODS = _split_csv(os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS"))
CORS_ALLOW_HEADERS = _split_csv(os.getenv("CORS_ALLOW_HEADERS", "Authorization,Content-Type,Accept,Origin,X-Requested-With"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
