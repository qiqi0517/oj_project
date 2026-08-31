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


def unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def unique_problem_id() -> str:
    return f"PERM_{uuid4().hex[:8]}"


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