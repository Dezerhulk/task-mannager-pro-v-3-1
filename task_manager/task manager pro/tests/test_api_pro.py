"""API endpoint tests for Task Manager Pro."""

import pytest


def register_user(client, user_data):
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    return response.json()


def login_user(client, email, password):
    response = client.post(
        "/api/auth/login",
        params={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    return data["access_token"], data["refresh_token"]


def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


def create_project(client, token, project_data):
    return client.post(
        "/api/projects",
        json=project_data,
        headers=auth_headers(token),
    )


def create_task(client, token, task_data):
    return client.post(
        "/api/tasks",
        json=task_data,
        headers=auth_headers(token),
    )


class TestUserAPI:
    def test_register_and_login(self, client, test_user_data):
        user = register_user(client, test_user_data)
        assert user["email"] == test_user_data["email"]

        access_token, refresh_token = login_user(
            client, test_user_data["email"], test_user_data["password"]
        )
        assert access_token
        assert refresh_token

    def test_get_user(self, client, test_user_data):
        user = register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        response = client.get(f"/api/users/{user['id']}", headers=auth_headers(token))
        assert response.status_code == 200
        assert response.json()["id"] == user["id"]

    def test_get_user_not_found(self, client, test_user_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        response = client.get("/api/users/99999", headers=auth_headers(token))
        assert response.status_code == 404

    def test_get_users_pagination(self, client, test_user_data):
        user = register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        for i in range(3):
            data = test_user_data.copy()
            data["username"] = f"user{i}"
            data["email"] = f"user{i}@example.com"
            register_user(client, data)

        response = client.get("/api/users?skip=0&limit=2", headers=auth_headers(token))
        assert response.status_code == 200
        assert len(response.json()) <= 2

    def test_update_user(self, client, test_user_data):
        user = register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        update_data = {"username": "newusername"}
        response = client.put(
            f"/api/users/{user['id']}",
            json=update_data,
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["username"] == "newusername"

    def test_delete_user(self, client, test_user_data):
        user = register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        response = client.delete(
            f"/api/users/{user['id']}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["deleted"] is True


class TestProjectAPI:
    def test_create_project(self, client, test_user_data, test_project_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        response = create_project(client, token, test_project_data)
        assert response.status_code == 200
        assert response.json()["title"] == test_project_data["title"]

    def test_get_project(self, client, test_user_data, test_project_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        response = client.get(
            f"/api/projects/{project_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["id"] == project_id

    def test_get_all_projects(self, client, test_user_data, test_project_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        create_project(client, token, test_project_data)
        response = client.get("/api/projects", headers=auth_headers(token))
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_projects(self, client, test_user_data, test_project_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        create_project(client, token, test_project_data)
        response = client.post(
            "/api/projects/search",
            json={"search": "Test"},
            headers=auth_headers(token),
        )
        assert response.status_code == 200

    def test_update_project(self, client, test_user_data, test_project_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        update_data = {"title": "Updated Title"}
        response = client.put(
            f"/api/projects/{project_id}",
            json=update_data,
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_delete_project(self, client, test_user_data, test_project_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        response = client.delete(
            f"/api/projects/{project_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["deleted"] is True

    def test_add_project_member(self, client, test_user_data, test_project_data):
        owner = test_user_data.copy()
        owner["username"] = "owner1"
        owner["email"] = "owner1@example.com"
        register_user(client, owner)
        owner_token, _ = login_user(client, owner["email"], owner["password"])

        member = test_user_data.copy()
        member["username"] = "member1"
        member["email"] = "member1@example.com"
        new_member = register_user(client, member)

        project_response = create_project(client, owner_token, test_project_data)
        project_id = project_response.json()["id"]

        response = client.post(
            f"/api/projects/{project_id}/members/{new_member['id']}",
            headers=auth_headers(owner_token),
        )
        assert response.status_code == 200
        assert response.json()["added"] is True


class TestTaskAPI:
    def test_create_task(self, client, test_user_data, test_project_data, test_task_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        task_payload = {**test_task_data, "project_id": project_id}
        response = create_task(client, token, task_payload)
        assert response.status_code == 200
        assert response.json()["title"] == test_task_data["title"]

    def test_get_task(self, client, test_user_data, test_project_data, test_task_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        task_payload = {**test_task_data, "project_id": project_id}
        task_response = create_task(client, token, task_payload)
        task_id = task_response.json()["id"]

        response = client.get(
            f"/api/tasks/{task_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["id"] == task_id

    def test_get_project_tasks(self, client, test_user_data, test_project_data, test_task_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        response = client.get(
            f"/api/projects/{project_id}/tasks",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_tasks(self, client, test_user_data, test_project_data, test_task_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        create_project(client, token, test_project_data)
        response = client.post(
            "/api/tasks/search",
            json={"search": "Test"},
            headers=auth_headers(token),
        )
        assert response.status_code == 200

    def test_update_task(self, client, test_user_data, test_project_data, test_task_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        task_payload = {**test_task_data, "project_id": project_id}
        task_response = create_task(client, token, task_payload)
        task_id = task_response.json()["id"]

        response = client.put(
            f"/api/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    def test_delete_task(self, client, test_user_data, test_project_data, test_task_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        task_payload = {**test_task_data, "project_id": project_id}
        task_response = create_task(client, token, task_payload)
        task_id = task_response.json()["id"]

        response = client.delete(
            f"/api/tasks/{task_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["deleted"] is True


class TestCommentAPI:
    def test_create_comment(self, client, test_user_data, test_project_data, test_task_data, test_comment_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        task_payload = {**test_task_data, "project_id": project_id}
        task_response = create_task(client, token, task_payload)
        task_id = task_response.json()["id"]

        response = client.post(
            f"/api/tasks/{task_id}/comments",
            json=test_comment_data,
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["content"] == test_comment_data["content"]

    def test_get_task_comments(self, client, test_user_data, test_project_data, test_task_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        project_response = create_project(client, token, test_project_data)
        project_id = project_response.json()["id"]

        task_payload = {**test_task_data, "project_id": project_id}
        task_response = create_task(client, token, task_payload)
        task_id = task_response.json()["id"]

        response = client.get(
            f"/api/tasks/{task_id}/comments",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTagAPI:
    def test_create_tag(self, client, test_user_data, test_tag_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        response = client.post(
            "/api/tags",
            json=test_tag_data,
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["name"] == test_tag_data["name"]

    def test_get_tag(self, client, test_user_data, test_tag_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        tag_response = client.post(
            "/api/tags",
            json=test_tag_data,
            headers=auth_headers(token),
        )
        tag_id = tag_response.json()["id"]

        response = client.get(
            f"/api/tags/{tag_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["id"] == tag_id

    def test_get_all_tags(self, client, test_user_data, test_tag_data):
        register_user(client, test_user_data)
        token, _ = login_user(client, test_user_data["email"], test_user_data["password"])

        client.post(
            "/api/tags",
            json=test_tag_data,
            headers=auth_headers(token),
        )
        response = client.get("/api/tags", headers=auth_headers(token))
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestHealthAndRoot:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()