import sqlite3
from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import DATABASE_PATH
from app.main import app
from app.repositories import problem_repository

TEST_PASSWORD = "secret1"


def unique_problem_id() -> str:
    return f"NEWP_{uuid4().hex[:8]}"


def unique_username() -> str:
    return f"testproblem_{uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def cleanup_problem_data() -> Generator[None, None, None]:
    yield
    with sqlite3.connect(DATABASE_PATH) as db:
        db.execute("DELETE FROM test_cases WHERE problem_id LIKE 'NEWP_%'")
        db.execute("DELETE FROM problems WHERE id LIKE 'NEWP_%'")
        db.execute("DELETE FROM users WHERE username LIKE 'testproblem_%'")
        db.commit()


def register_and_login(client: TestClient) -> dict:
    username = unique_username()
    register_response = client.post(
        "/api/users/",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert register_response.status_code == status.HTTP_200_OK
    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == status.HTTP_200_OK
    return register_response.json()["data"]


def login_admin(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admintestpassword"},
    )
    assert response.status_code == status.HTTP_200_OK


def make_problem(problem_id: str | None = None) -> dict:
    return {
        "id": problem_id or unique_problem_id(),
        "title": "A+B",
        "description": "Add two integers.",
        "input_description": "Two integers.",
        "output_description": "Their sum.",
        "samples": [{"input": "1 2\n", "output": "3\n"}],
        "constraints": "Integers fit in 32 bits.",
        "testcases": [
            {"input": "1 2\n", "output": "3\n"},
            {"input": "-1 2\n", "output": "1\n"},
        ],
    }


def test_unauthenticated_problem_operations_return_401_before_body_errors() -> None:
    problem_id = unique_problem_id()
    with TestClient(app) as client:
        responses = [
            client.get("/api/problems/"),
            client.get(f"/api/problems/{problem_id}"),
            client.post("/api/problems/", json={}),
            client.put(f"/api/problems/{problem_id}", json={}),
            client.delete(f"/api/problems/{problem_id}"),
        ]
    assert all(
        response.status_code == status.HTTP_401_UNAUTHORIZED for response in responses
    )


def test_logged_in_user_can_create_list_view_and_update_problem() -> None:
    problem = make_problem()
    with TestClient(app) as client:
        register_and_login(client)
        create_response = client.post("/api/problems/", json=problem)
        list_response = client.get("/api/problems/")
        detail_response = client.get(f"/api/problems/{problem['id']}")

        updated = dict(problem)
        updated["title"] = "Updated A+B"
        update_response = client.put(
            f"/api/problems/{problem['id']}",
            json=updated,
        )

    assert create_response.status_code == status.HTTP_200_OK
    assert create_response.json()["msg"] == "add success"
    assert create_response.json()["data"] == {"id": problem["id"]}
    assert {"id": problem["id"], "title": problem["title"]} in list_response.json()[
        "data"
    ]
    detail = detail_response.json()["data"]
    assert detail["testcases"] == problem["testcases"]
    assert detail["hint"] == ""
    assert detail["source"] == ""
    assert detail["tags"] == []
    assert detail["time_limit"] == 3.0
    assert detail["memory_limit"] == 128
    assert detail["author"] == ""
    assert detail["difficulty"] == ""
    assert "public_cases" not in detail
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["msg"] == "update success"
    assert update_response.json()["data"] == {"id": problem["id"]}


def test_duplicate_missing_fields_and_id_mismatch() -> None:
    problem = make_problem()
    with TestClient(app) as client:
        register_and_login(client)
        assert client.post("/api/problems/", json=problem).status_code == 200
        duplicate = client.post("/api/problems/", json=problem)
        missing = client.post(
            "/api/problems/",
            json={"id": unique_problem_id()},
        )
        changed_id = dict(problem)
        changed_id["id"] = unique_problem_id()
        mismatch = client.put(
            f"/api/problems/{problem['id']}",
            json=changed_id,
        )

    assert duplicate.status_code == status.HTTP_409_CONFLICT
    assert missing.status_code == status.HTTP_400_BAD_REQUEST
    assert mismatch.status_code == status.HTTP_400_BAD_REQUEST


def test_only_admin_can_delete_problem() -> None:
    problem = make_problem()
    with TestClient(app) as client:
        register_and_login(client)
        client.post("/api/problems/", json=problem)
        denied = client.delete(f"/api/problems/{problem['id']}")
        client.post("/api/auth/logout")
        login_admin(client)
        deleted = client.delete(f"/api/problems/{problem['id']}")
        missing = client.get(f"/api/problems/{problem['id']}")

    assert denied.status_code == status.HTTP_403_FORBIDDEN
    assert deleted.status_code == status.HTTP_200_OK
    assert deleted.json()["msg"] == "delete success"
    assert deleted.json()["data"] == {"id": problem["id"]}
    assert missing.status_code == status.HTTP_404_NOT_FOUND


def test_only_admin_can_change_log_visibility() -> None:
    problem = make_problem()
    with TestClient(app) as client:
        register_and_login(client)
        client.post("/api/problems/", json=problem)
        denied = client.put(
            f"/api/problems/{problem['id']}/log_visibility",
            json={"public_cases": True},
        )
        client.post("/api/auth/logout")
        login_admin(client)
        updated = client.put(
            f"/api/problems/{problem['id']}/log_visibility",
            json={"public_cases": True},
        )

    assert denied.status_code == status.HTTP_403_FORBIDDEN
    assert updated.status_code == status.HTTP_200_OK
    assert updated.json()["data"] == {
        "problem_id": problem["id"],
        "public_cases": True,
    }


def test_problem_payload_cannot_bypass_log_visibility_permission() -> None:
    problem = make_problem()
    problem["public_cases"] = True
    with TestClient(app) as client:
        register_and_login(client)
        response = client.post("/api/problems/", json=problem)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_unknown_database_error_returns_sanitized_500(monkeypatch) -> None:
    async def fail_create_problem(*args, **kwargs):
        raise RuntimeError("private database failure")

    monkeypatch.setattr(problem_repository, "create_problem", fail_create_problem)
    with TestClient(app, raise_server_exceptions=False) as client:
        register_and_login(client)
        response = client.post("/api/problems/", json=make_problem())

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["msg"] == "internal server error"
    assert "private database failure" not in response.text
