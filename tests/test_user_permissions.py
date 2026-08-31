import sqlite3
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import DATABASE_PATH
from app.main import app
from app.models.enums import UserRole
from app.utils.auth import require_admin
from app.utils.exceptions import AppError

TEST_PASSWORD = "password123"
USERNAME_PREFIX = "up_"
PROBLEM_PREFIX = "PERM_"


@pytest.fixture(autouse=True)
def cleanup_user_permission_test_data():
    yield
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "DELETE FROM test_cases WHERE problem_id LIKE ?",
            (PROBLEM_PREFIX + "%",),
        )
        connection.execute(
            "DELETE FROM problems WHERE id LIKE ?",
            (PROBLEM_PREFIX + "%",),
        )
        connection.execute(
            "DELETE FROM users WHERE username LIKE ?",
            (USERNAME_PREFIX + "%",),
        )
        connection.commit()


def unique_username(prefix: str) -> str:
    return f"{USERNAME_PREFIX}{prefix}_{uuid4().hex[:8]}"


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


def test_inactive_user_cannot_login() -> None:
    username = unique_username("inactive")
    with TestClient(app) as client:
        register_user(client, username)
        disable_user(username)
        response = client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": TEST_PASSWORD,
            },
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["code"] == status.HTTP_403_FORBIDDEN


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


# Role and resource permission tests
def unique_problem_id() -> str:
    return f"{PROBLEM_PREFIX}{uuid4().hex[:8]}"


def set_user_role(
    username: str,
    role: UserRole,
) -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE users
            SET role = ?
            WHERE username = ?
            """,
            (
                role.value,
                username,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def disable_user(username: str) -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE users
            SET is_active = 0
            WHERE username = ?
            """,
            (username,),
        )
        connection.commit()
    finally:
        connection.close()


def register_user(
    client: TestClient,
    username: str,
) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


def login_user(
    client: TestClient,
    username: str,
) -> None:
    response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == status.HTTP_200_OK


def prepare_user(
    client: TestClient,
    role: UserRole,
) -> str:
    username = unique_username(role.value)
    register_user(
        client,
        username,
    )
    if role != UserRole.STUDENT:
        set_user_role(
            username,
            role,
        )
    login_user(
        client,
        username,
    )
    return username


def make_problem(
    problem_id: str,
) -> dict:
    return {
        "id": problem_id,
        "title": "A+B Problem",
        "description": "输入两个整数，输出它们的和。",
        "input_description": "输入两个整数 a 和 b。",
        "output_description": "输出 a + b。",
        "samples": [
            {
                "input": "1 2\n",
                "output": "3\n",
            }
        ],
        "constraints": "|a|, |b| <= 10^9",
        "time_limit": 1.0,
        "memory_limit": 128,
        "difficulty": "easy",
        "tags": [
            "基础",
            "输入输出",
        ],
        "test_cases": [
            {
                "case_id": "case_01",
                "input": "1 2\n",
                "output": "3\n",
                "score": 50,
                "is_hidden": False,
            },
            {
                "case_id": "case_02",
                "input": "-1 2\n",
                "output": "1\n",
                "score": 50,
                "is_hidden": True,
            },
        ],
    }


def make_problem_update() -> dict:
    return {
        "title": "Updated A+B Problem",
        "description": "输入两个整数，输出它们的和。",
        "input_description": "输入两个整数 a 和 b。",
        "output_description": "输出 a + b。",
        "samples": [
            {
                "input": "2 3\n",
                "output": "5\n",
            }
        ],
        "constraints": "|a|, |b| <= 10^9",
        "time_limit": 2.0,
        "memory_limit": 256,
        "difficulty": "easy",
        "tags": [
            "基础",
        ],
        "test_cases": [
            {
                "case_id": "case_01",
                "input": "2 3\n",
                "output": "5\n",
                "score": 100,
                "is_hidden": True,
            }
        ],
    }


def test_unauthenticated_user_cannot_access_protected_api() -> None:
    with TestClient(app) as client:
        me_response = client.get(
            "/api/auth/me"
        )
        problems_response = client.get(
            "/api/problems"
        )
    assert (me_response.status_code == status.HTTP_401_UNAUTHORIZED)
    assert (problems_response.status_code == status.HTTP_401_UNAUTHORIZED)


def test_student_can_read_problems_but_cannot_manage_them() -> None:
    problem_id = unique_problem_id()
    with TestClient(app) as client:
        # teacher 创建一个真实 Problem
        prepare_user(
            client,
            UserRole.TEACHER,
        )
        create_response = client.post(
            "/api/problems",
            json=make_problem(problem_id),
        )
        assert (create_response.status_code == status.HTTP_201_CREATED)
        # teacher logout
        client.post("/api/auth/logout")

        # student 登录
        prepare_user(
            client,
            UserRole.STUDENT,
        )
        # student 可以查看列表
        list_response = client.get(
            "/api/problems"
        )
        assert (list_response.status_code == status.HTTP_200_OK)
        # student 可以查看题目详情
        detail_response = client.get(
            f"/api/problems/{problem_id}"
        )
        assert (detail_response.status_code == status.HTTP_200_OK)
        # student 不能创建题目
        post_response = client.post(
            "/api/problems",
            json=make_problem(
                unique_problem_id()
            ),
        )
        assert (post_response.status_code == status.HTTP_403_FORBIDDEN)
        # student 不能修改题目
        put_response = client.put(
            f"/api/problems/{problem_id}",
            json=make_problem_update(),
        )
        assert (put_response.status_code == status.HTTP_403_FORBIDDEN)
        # student 不能删除题目
        delete_response = client.delete(
            f"/api/problems/{problem_id}"
        )
        assert (delete_response.status_code == status.HTTP_403_FORBIDDEN)


def test_teacher_can_manage_problem() -> None:
    problem_id = unique_problem_id()
    with TestClient(app) as client:
        prepare_user(
            client,
            UserRole.TEACHER,
        )

        create_response = client.post(
            "/api/problems",
            json=make_problem(problem_id),
        )
        assert (create_response.status_code == status.HTTP_201_CREATED)

        update_response = client.put(
            f"/api/problems/{problem_id}",
            json=make_problem_update(),
        )
        assert (update_response.status_code == status.HTTP_200_OK)

        delete_response = client.delete(
            f"/api/problems/{problem_id}"
        )
        assert (delete_response.status_code == status.HTTP_200_OK)


def test_admin_has_teacher_permissions() -> None:
    problem_id = unique_problem_id()
    with TestClient(app) as client:
        prepare_user(
            client,
            UserRole.ADMIN,
        )
        create_response = client.post(
            "/api/problems",
            json=make_problem(problem_id),
        )
        assert (create_response.status_code == status.HTTP_201_CREATED)

        update_response = client.put(
            f"/api/problems/{problem_id}",
            json=make_problem_update(),
        )
        assert (update_response.status_code == status.HTTP_200_OK)

        delete_response = client.delete(
            f"/api/problems/{problem_id}"
        )
        assert (delete_response.status_code == status.HTTP_200_OK)


@pytest.mark.asyncio
async def test_teacher_cannot_pass_require_admin() -> None:
    teacher = {
        "role": UserRole.TEACHER.value,
    }
    with pytest.raises(AppError) as exc_info:
        await require_admin(teacher)
    assert (exc_info.value.status_code == status.HTTP_403_FORBIDDEN)


@pytest.mark.asyncio
async def test_admin_can_pass_require_admin() -> None:
    admin = {
        "role": UserRole.ADMIN.value,
    }
    result = await require_admin(admin)
    assert result == admin


def test_disabled_old_session_cannot_access_protected_api() -> None:
    username = unique_username("disabled_session")
    with TestClient(app) as client:
        register_user(
            client,
            username,
        )
        login_user(
            client,
            username,
        )
        # 当前 Session 此时是有效的
        before_disable = client.get(
            "/api/problems"
        )
        assert (before_disable.status_code == status.HTTP_200_OK)
        # 模拟管理员在用户已经登录后将其禁用
        disable_user(username)
        # 注意：没有 logout，也没有重新 login
        # 继续使用原来的 Cookie
        after_disable = client.get(
            "/api/problems"
        )
        assert (after_disable.status_code == status.HTTP_403_FORBIDDEN)
        assert (after_disable.json()["code"] == status.HTTP_403_FORBIDDEN)
