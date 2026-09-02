import json
import sqlite3
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import DATABASE_PATH
from app.main import app

TEST_PASSWORD = "secret1"


def unique_username(label: str) -> str:
    return f"testnew_{label}_{uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def cleanup_test_users():
    yield
    with sqlite3.connect(DATABASE_PATH) as db:
        rows = db.execute(
            "SELECT id FROM users WHERE username LIKE 'testnew_%'"
        ).fetchall()
        user_ids = [row[0] for row in rows]
        for user_id in user_ids:
            db.execute(
                "DELETE FROM audit_logs WHERE operator_id = ? OR target_id = ?",
                (user_id, user_id),
            )
        db.execute("DELETE FROM users WHERE username LIKE 'testnew_%'")
        db.commit()


def register(client: TestClient, username: str) -> dict:
    response = client.post(
        "/api/users/",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "register success"
    return response.json()["data"]


def login(
    client: TestClient,
    username: str,
    password: str = TEST_PASSWORD,
) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "login success"
    return response.json()["data"]


def login_admin(client: TestClient) -> dict:
    return login(client, "admin", "admintestpassword")


def test_register_uses_new_path_fields_and_role() -> None:
    username = unique_username("register")
    with TestClient(app) as client:
        response = client.post(
            "/api/users/",
            json={"username": username, "password": TEST_PASSWORD},
        )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["code"] == status.HTTP_200_OK
    assert body["msg"] == "register success"
    assert set(body) == {"code", "msg", "data"}
    assert body["data"]["username"] == username
    assert body["data"]["role"] == "user"
    assert body["data"]["submit_count"] == 0
    assert body["data"]["resolve_count"] == 0
    assert len(body["data"]["join_time"]) == 10
    assert "password" not in body["data"]


@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"username": "ab", "password": TEST_PASSWORD}, 400),
        ({"username": "a" * 41, "password": TEST_PASSWORD}, 400),
        ({"username": "valid_name", "password": "12345"}, 400),
        (
            {
                "username": "valid_name",
                "password": TEST_PASSWORD,
                "role": "admin",
            },
            400,
        ),
    ],
)
def test_register_validation_returns_400(
    payload: dict,
    expected_status: int,
) -> None:
    with TestClient(app) as client:
        response = client.post("/api/users/", json=payload)
    assert response.status_code == expected_status
    assert response.json()["code"] == expected_status
    assert "msg" in response.json()


def test_unknown_api_uses_standard_error_response() -> None:
    with TestClient(app) as client:
        response = client.get("/api/not-found")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "code": status.HTTP_404_NOT_FOUND,
        "msg": "Not Found",
        "data": None,
    }


def test_duplicate_username_returns_400() -> None:
    username = unique_username("duplicate")
    with TestClient(app) as client:
        register(client, username)
        response = client.post(
            "/api/users/",
            json={"username": username, "password": TEST_PASSWORD},
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_initial_admin_and_logout_requires_session() -> None:
    with TestClient(app) as client:
        admin = login_admin(client)
        assert admin == {
            "user_id": admin["user_id"],
            "username": "admin",
            "role": "admin",
        }
        logout = client.post("/api/auth/logout")
        second_logout = client.post("/api/auth/logout")

    assert logout.status_code == status.HTTP_200_OK
    assert logout.json()["msg"] == "logout success"
    assert logout.json()["data"] is None
    assert second_logout.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_login_has_same_message() -> None:
    username = unique_username("login")
    with TestClient(app) as client:
        register(client, username)
        wrong_password = client.post(
            "/api/auth/login",
            json={"username": username, "password": "incorrect"},
        )
        unknown_user = client.post(
            "/api/auth/login",
            json={"username": unique_username("unknown"), "password": "incorrect"},
        )
    assert wrong_password.status_code == status.HTTP_401_UNAUTHORIZED
    assert unknown_user.status_code == status.HTTP_401_UNAUTHORIZED
    assert wrong_password.json()["msg"] == unknown_user.json()["msg"]


def test_user_detail_is_limited_to_owner_or_admin() -> None:
    first_name = unique_username("owner")
    second_name = unique_username("other")
    with TestClient(app) as client:
        first = register(client, first_name)
        second = register(client, second_name)
        login(client, first_name)
        own_response = client.get(f"/api/users/{first['user_id']}")
        other_response = client.get(f"/api/users/{second['user_id']}")
        client.post("/api/auth/logout")
        login_admin(client)
        admin_response = client.get(f"/api/users/{second['user_id']}")

    assert own_response.status_code == status.HTTP_200_OK
    assert other_response.status_code == status.HTTP_403_FORBIDDEN
    assert admin_response.status_code == status.HTTP_200_OK


def test_admin_can_create_admin_list_users_and_update_role() -> None:
    username = unique_username("managed")
    new_admin_name = unique_username("admin")
    with TestClient(app) as client:
        user = register(client, username)
        unauthenticated_create = client.post(
            "/api/users/admin",
            json={"username": new_admin_name, "password": TEST_PASSWORD},
        )
        login_admin(client)
        create_admin_response = client.post(
            "/api/users/admin",
            json={"username": new_admin_name, "password": TEST_PASSWORD},
        )
        role_response = client.put(
            f"/api/users/{user['user_id']}/role",
            json={"role": "banned"},
        )
        list_response = client.get("/api/users/?page_size=2")

    assert unauthenticated_create.status_code == status.HTTP_401_UNAUTHORIZED
    assert create_admin_response.status_code == status.HTTP_200_OK
    assert create_admin_response.json()["msg"] == "success"
    assert create_admin_response.json()["data"] == {
        "user_id": create_admin_response.json()["data"]["user_id"],
        "username": new_admin_name,
    }
    assert role_response.status_code == status.HTTP_200_OK
    assert role_response.json()["data"]["role"] == "banned"
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.json()["data"]["users"]) <= 2
    assert list_response.json()["data"]["total"] >= 3

    with sqlite3.connect(DATABASE_PATH) as db:
        row = db.execute(
            """
            SELECT action, target_id, detail
            FROM audit_logs
            WHERE target_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user["user_id"],),
        ).fetchone()
    assert row is not None
    assert row[0] == "UPDATE_USER_ROLE"
    assert row[1] == user["user_id"]
    assert json.loads(row[2]) == {"role": "banned"}


def test_page_without_page_size_returns_400() -> None:
    with TestClient(app) as client:
        login_admin(client)
        response = client.get("/api/users/?page=2")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_banned_user_cannot_login_or_reuse_old_session() -> None:
    username = unique_username("banned")
    with TestClient(app) as user_client, TestClient(app) as admin_client:
        user = register(user_client, username)
        login(user_client, username)
        login_admin(admin_client)
        update_response = admin_client.put(
            f"/api/users/{user['user_id']}/role",
            json={"role": "banned"},
        )
        old_session_response = user_client.get(f"/api/users/{user['user_id']}")
        login_response = user_client.post(
            "/api/auth/login",
            json={"username": username, "password": TEST_PASSWORD},
        )

    assert update_response.status_code == status.HTTP_200_OK
    assert old_session_response.status_code == status.HTTP_403_FORBIDDEN
    assert login_response.status_code == status.HTTP_403_FORBIDDEN


def test_openapi_contains_response_models_for_all_api_operations() -> None:
    openapi = app.openapi()
    missing_response_schemas = []
    for path, path_item in openapi["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            schema = (
                operation.get("responses", {})
                .get("200", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema")
            )
            if schema is None:
                missing_response_schemas.append(f"{method.upper()} {path}")

    component_schemas = openapi["components"]["schemas"]
    assert missing_response_schemas == []
    assert "SubmissionCreateResponse" in component_schemas
    assert "UserRoleUpdateResponse" in component_schemas
