import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in .env or environment")

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
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
