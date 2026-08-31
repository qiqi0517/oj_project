import sqlite3
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from app.config import DATABASE_PATH
from app.main import app

TEST_PASSWORD = "password123"


def unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def get_user_from_db(username: str) -> sqlite3.Row | None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.execute(
            """
            SELECT
                id,
                username,
                password_hash,
                role,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        return cursor.fetchone()
    finally:
        connection.close()


def assert_no_password_fields(data: dict) -> None:
    assert "password" not in data
    assert "password_hash" not in data


def test_register_success() -> None:
    username = unique_username("student")
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["code"] == status.HTTP_201_CREATED
    assert body["data"]["username"] == username
    assert body["data"]["role"] == "student"
    assert body["data"]["is_active"] is True
    assert_no_password_fields(body["data"])

    user = get_user_from_db(username)
    assert user is not None
    assert user["username"] == username
    assert user["role"] == "student"
    assert user["is_active"] == 1
    assert user["password_hash"] != TEST_PASSWORD


def test_register_duplicate_username() -> None:
    username = unique_username("duplicate")
    with TestClient(app) as client:
        first_response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )
        second_response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )
    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_409_CONFLICT
    assert (
        second_response.json()["code"]
        == status.HTTP_409_CONFLICT
    )


def test_register_username_too_short() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "username": "ab",
                "password": TEST_PASSWORD,
            },
        )
    assert (response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT)
    assert (response.json()["code"] == status.HTTP_422_UNPROCESSABLE_CONTENT)


def test_register_username_too_long() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "username": "a" * 33,
                "password": TEST_PASSWORD,
            },
        )
    assert (response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT)


def test_register_password_too_short() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "username": unique_username("student"),
                "password": "1234567",
            },
        )
    assert (response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT)


def test_register_cannot_specify_admin_role() -> None:
    username = unique_username("hacker")
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": TEST_PASSWORD,
                "role": "admin",
            },
        )
    assert (response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT)
    user = get_user_from_db(username)
    assert user is None


def test_login_success_and_me() -> None:
    username = unique_username("login")
    with TestClient(app) as client:
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )
        assert (register_response.status_code == status.HTTP_201_CREATED)

        login_response = client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )
        assert (login_response.status_code == status.HTTP_200_OK)
        login_body = login_response.json()
        assert login_body["code"] == status.HTTP_200_OK
        assert login_body["data"]["username"] == username
        assert_no_password_fields(login_body["data"])
        assert "session" in client.cookies

        me_response = client.get("/api/auth/me")
        assert (me_response.status_code == status.HTTP_200_OK)
        me_body = me_response.json()
        assert me_body["data"]["username"] == username
        assert_no_password_fields(me_body["data"])


def test_login_invalid_username_and_password_have_same_message() -> None:
    username = unique_username("loginerror")
    with TestClient(app) as client:
        client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )
        unknown_user_response = client.post(
            "/api/auth/login",
            json={
                "username": unique_username("missing"),
                "password": TEST_PASSWORD,
            },
        )
        wrong_password_response = client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": "wrongpassword",
            },
        )
    assert (unknown_user_response.status_code == status.HTTP_401_UNAUTHORIZED)
    assert (wrong_password_response.status_code == status.HTTP_401_UNAUTHORIZED)
    assert (unknown_user_response.json()["message"] == wrong_password_response.json()["message"])


def test_me_without_login() -> None:
    with TestClient(app) as client:
        response = client.get("/api/auth/me")
    assert (response.status_code == status.HTTP_401_UNAUTHORIZED)
    assert (response.json()["code"] == status.HTTP_401_UNAUTHORIZED)


def test_logout_invalidates_session() -> None:
    username = unique_username("logout")
    with TestClient(app) as client:
        client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )
        client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )
        me_before_logout = client.get("/api/auth/me")
        assert (me_before_logout.status_code == status.HTTP_200_OK)

        logout_response = client.post("/api/auth/logout")
        assert (logout_response.status_code == status.HTTP_200_OK)
        assert logout_response.json()["data"] is None

        me_after_logout = client.get("/api/auth/me")
        assert (me_after_logout.status_code == status.HTTP_401_UNAUTHORIZED)