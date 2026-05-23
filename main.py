import uvicorn

from task_api import app


def main() -> None:
    """Start the FastAPI application."""
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
