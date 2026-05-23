import importlib
import sys

import pytest


@pytest.fixture(autouse=True)
def test_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_KEY", "testsecretkey_long_and_secure_12345")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test_tasks.db'}")
    monkeypatch.setenv("LOG_FILE", str(tmp_path / 'test_app.log'))
    monkeypatch.setenv("RATE_LIMIT", "100")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_SECONDS", "3600")

    for module_name in ["config", "auth", "database", "storage", "worker", "task_api"]:
        if module_name in sys.modules:
            del sys.modules[module_name]

    import config  # noqa: F401
    import auth  # noqa: F401
    import database  # noqa: F401
    import storage  # noqa: F401
    import worker  # noqa: F401
    import task_api  # noqa: F401

    importlib.reload(config)
    importlib.reload(auth)
    importlib.reload(database)
    importlib.reload(storage)
    importlib.reload(worker)
    importlib.reload(task_api)


@pytest.fixture
def app():
    import task_api

    importlib.reload(task_api)
    return task_api.app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client
