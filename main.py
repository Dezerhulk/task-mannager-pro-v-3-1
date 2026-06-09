import os

import uvicorn

from task_api import app


def main() -> None:
    """Start the FastAPI application in development or production mode."""
    env_name = os.getenv("APP_ENV", "development").lower()
    reload = env_name == "development" and os.getenv("RELOAD", "true").lower() in {"1", "true", "yes", "on"}
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    if env_name == "production":
        uvicorn.run(app, host=host, port=port, reload=False, workers=int(os.getenv("UVICORN_WORKERS", "1")))
        return

    uvicorn.run(app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
