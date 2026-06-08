import os

import uvicorn

from task_api import app


def main() -> None:
    """Start the FastAPI application."""
    reload = os.getenv("RELOAD", "false").lower() in {"1", "true", "yes", "on"}
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=reload)


if __name__ == "__main__":
    main()
