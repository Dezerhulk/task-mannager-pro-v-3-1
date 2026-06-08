import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "replace-me-with-a-long-random-secret")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
RATE_LIMIT_STR = os.getenv("RATE_LIMIT")
if not RATE_LIMIT_STR:
    raise RuntimeError("RATE_LIMIT must be set in .env or environment")
RATE_LIMIT = int(RATE_LIMIT_STR)
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "3600"))
REFRESH_TOKEN_EXPIRE_SECONDS = int(os.getenv("REFRESH_TOKEN_EXPIRE_SECONDS", "1209600"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() in {"1", "true", "yes", "on"}
CORS_ALLOW_METHODS = [method.strip() for method in os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",") if method.strip()]
CORS_ALLOW_HEADERS = [header.strip() for header in os.getenv("CORS_ALLOW_HEADERS", "Authorization,Content-Type,Accept,Origin,X-Requested-With").split(",") if header.strip()]
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
