import importlib
import sys
import time


def get_token(client, username="alice", password="Alice12345!"):
    # Try to register first (will fail if user exists, which is fine)
    client.post("/register", json={"username": username, "password": password})
    
    # Now login
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert token
    return token


def test_token_creation(client):
    token = get_token(client)
    assert token is not None


def test_create_task_and_get_status(client):
    token = get_token(client)
    response = client.post(
        "/tasks",
        json={"data": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    for _ in range(10):
        response = client.get(
            f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == "done":
            break
        time.sleep(0.5)

    assert payload["id"] == task_id
    assert payload["status"] == "done"
    assert payload["result"] == "HELLO"


def test_forbidden_task_access(client):
    alice_token = get_token(client, username="alice", password="Alice12345!")
    response = client.post(
        "/tasks",
        json={"data": "secret"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    bob_token = get_token(client, username="bob", password="BobPass123!")
    response = client.get(
        f"/tasks/{task_id}", headers={"Authorization": f"Bearer {bob_token}"}
    )
    assert response.status_code == 403


def test_rate_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT", "1")

    for module_name in ["config", "storage", "task_api"]:
        if module_name in sys.modules:
            del sys.modules[module_name]

    import config  # noqa: F401
    import storage  # noqa: F401
    import task_api  # noqa: F401
    importlib.reload(config)
    importlib.reload(storage)
    importlib.reload(task_api)

    from fastapi.testclient import TestClient

    with TestClient(task_api.app) as client:
        token = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post("/tasks", json={"data": "one"}, headers=headers)
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        response = client.get(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 429
