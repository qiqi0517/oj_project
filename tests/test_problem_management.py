import sqlite3
from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import (
    DATABASE_PATH,
    INITIAL_ADMIN_PASSWORD,
    INITIAL_ADMIN_USERNAME,
)
from app.main import app
from app.models.enums import UserRole
from app.utils.time import to_iso8601, utc_now


TEST_PASSWORD = "password123"
USERNAME_PREFIX = "pytest_d2_"
PROBLEM_PREFIX = "PYTEST_D2_"
SUBMISSION_PREFIX = "pytest_d2_submission_"


@pytest.fixture(autouse=True)
def cleanup_problem_test_data():
    yield
    cleanup_test_data()


def cleanup_test_data() -> None:
    with sqlite3.connect(DATABASE_PATH) as db:
        db.execute(
            "DELETE FROM judge_logs WHERE submission_id LIKE ?",
            (SUBMISSION_PREFIX + "%",),
        )
        db.execute(
            "DELETE FROM submissions WHERE id LIKE ?",
            (SUBMISSION_PREFIX + "%",),
        )
        db.execute(
            "DELETE FROM test_cases WHERE problem_id LIKE ?",
            (PROBLEM_PREFIX + "%",),
        )
        db.execute(
            "DELETE FROM problems WHERE id LIKE ?",
            (PROBLEM_PREFIX + "%",),
        )
        db.execute(
            "DELETE FROM users WHERE username LIKE ?",
            (USERNAME_PREFIX + "%",),
        )
        db.commit()


def unique_username(role: UserRole) -> str:
    return f"{USERNAME_PREFIX}{role.value}_{uuid4().hex[:8]}"


def unique_problem_id() -> str:
    return f"{PROBLEM_PREFIX}{uuid4().hex[:8]}"


def register_user(client: TestClient, role: UserRole) -> tuple[str, str]:
    username = unique_username(role)
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    user_id = response.json()["data"]["id"]
    if role != UserRole.STUDENT:
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (role.value, user_id),
            )
            db.commit()
    return username, user_id


def login(client: TestClient, username: str, password: str = TEST_PASSWORD) -> None:
    response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == status.HTTP_200_OK


def login_as(client: TestClient, username: str, password: str = TEST_PASSWORD) -> None:
    client.post("/api/auth/logout")
    login(client, username, password)


def make_problem(problem_id: str) -> dict:
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
        "tags": ["基础", "输入输出"],
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


def make_update() -> dict:
    return {
        "title": "Updated A+B Problem",
        "description": "更新后的题目描述。",
        "input_description": "输入两个整数。",
        "output_description": "输出它们的和。",
        "samples": [{"input": "2 3\n", "output": "5\n"}],
        "constraints": "|a|, |b| <= 10^9",
        "time_limit": 2.0,
        "memory_limit": 256,
        "difficulty": "medium",
        "tags": ["更新"],
        "test_cases": [
            {
                "case_id": "updated_case",
                "input": "2 3\n",
                "output": "5\n",
                "score": 100,
                "is_hidden": True,
            }
        ],
    }


def create_problem_as_teacher(
    client: TestClient,
) -> tuple[str, str, str]:
    teacher_name, teacher_id = register_user(client, UserRole.TEACHER)
    login(client, teacher_name)
    problem_id = unique_problem_id()
    response = client.post(
        "/api/problems",
        json=make_problem(problem_id),
    )
    assert response.status_code == status.HTTP_201_CREATED
    return problem_id, teacher_name, teacher_id


def test_problem_create_duplicate_and_field_validation() -> None:
    with TestClient(app) as client:
        problem_id, _, _ = create_problem_as_teacher(client)

        duplicate_response = client.post(
            "/api/problems",
            json=make_problem(problem_id),
        )
        assert duplicate_response.status_code == status.HTTP_409_CONFLICT

        missing_title = make_problem(unique_problem_id())
        missing_title.pop("title")
        invalid_id = make_problem("invalid id")
        no_samples = make_problem(unique_problem_id())
        no_samples["samples"] = []
        invalid_score = make_problem(unique_problem_id())
        invalid_score["test_cases"][0]["score"] = 40

        for payload in (
            missing_title,
            invalid_id,
            no_samples,
            invalid_score,
        ):
            response = client.post("/api/problems", json=payload)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_student_list_and_detail_hide_test_cases() -> None:
    with TestClient(app) as client:
        problem_id, _, _ = create_problem_as_teacher(client)
        student_name, _ = register_user(client, UserRole.STUDENT)
        login_as(client, student_name)

        list_response = client.get("/api/problems")
        assert list_response.status_code == status.HTTP_200_OK
        list_data = list_response.json()["data"]
        assert "items" in list_data
        item = next(
            item for item in list_data["items"] if item["id"] == problem_id
        )
        assert {
            "id",
            "title",
            "difficulty",
            "tags",
            "time_limit",
            "memory_limit",
        } <= set(item)
        assert "test_cases" not in item

        detail_response = client.get(f"/api/problems/{problem_id}")
        assert detail_response.status_code == status.HTTP_200_OK
        detail = detail_response.json()["data"]
        assert detail["description"]
        assert detail["samples"]
        assert "test_cases" not in detail


def test_teacher_and_admin_detail_include_hidden_test_cases() -> None:
    with TestClient(app) as client:
        problem_id, teacher_name, _ = create_problem_as_teacher(client)

        for username, password in (
            (teacher_name, TEST_PASSWORD),
            (INITIAL_ADMIN_USERNAME, INITIAL_ADMIN_PASSWORD),
        ):
            login_as(client, username, password)
            response = client.get(f"/api/problems/{problem_id}")
            assert response.status_code == status.HTTP_200_OK
            test_cases = response.json()["data"]["test_cases"]
            hidden_case = next(case for case in test_cases if case["is_hidden"])
            assert hidden_case["input"] == "-1 2\n"
            assert hidden_case["output"] == "1\n"


def test_missing_problem_returns_unified_404() -> None:
    with TestClient(app) as client:
        student_name, _ = register_user(client, UserRole.STUDENT)
        login(client, student_name)
        response = client.get(f"/api/problems/{unique_problem_id()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["code"] == status.HTTP_404_NOT_FOUND
    assert response.json()["data"] is None


def test_problem_update_permissions_validation_and_persistence() -> None:
    with TestClient(app) as client:
        problem_id, teacher_name, _ = create_problem_as_teacher(client)
        student_name, _ = register_user(client, UserRole.STUDENT)

        login_as(client, student_name)
        student_response = client.put(
            f"/api/problems/{problem_id}",
            json=make_update(),
        )
        assert student_response.status_code == status.HTTP_403_FORBIDDEN

        login_as(client, teacher_name)
        valid_update = make_update()
        update_response = client.put(
            f"/api/problems/{problem_id}",
            json=valid_update,
        )
        assert update_response.status_code == status.HTTP_200_OK
        updated = update_response.json()["data"]
        assert updated["id"] == problem_id
        assert updated["title"] == valid_update["title"]
        assert updated["test_cases"] == valid_update["test_cases"]

        invalid_update = deepcopy(valid_update)
        invalid_update["title"] = "Should Not Persist"
        invalid_update["test_cases"][0]["score"] = 99
        invalid_response = client.put(
            f"/api/problems/{problem_id}",
            json=invalid_update,
        )
        assert invalid_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        persisted_response = client.get(f"/api/problems/{problem_id}")
        persisted = persisted_response.json()["data"]
        assert persisted["title"] == valid_update["title"]
        assert persisted["test_cases"] == valid_update["test_cases"]

        id_update = deepcopy(valid_update)
        id_update["id"] = "P9999"
        id_response = client.put(
            f"/api/problems/{problem_id}",
            json=id_update,
        )
        assert id_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert client.get(
            f"/api/problems/{problem_id}"
        ).json()["data"]["id"] == problem_id

        missing_response = client.put(
            f"/api/problems/{unique_problem_id()}",
            json=valid_update,
        )
        assert missing_response.status_code == status.HTTP_404_NOT_FOUND


def test_problem_delete_permissions_and_preserves_history() -> None:
    with TestClient(app) as client:
        problem_id, teacher_name, teacher_id = create_problem_as_teacher(client)
        student_name, _ = register_user(client, UserRole.STUDENT)

        login_as(client, student_name)
        student_response = client.delete(f"/api/problems/{problem_id}")
        assert student_response.status_code == status.HTTP_403_FORBIDDEN

        submission_id = SUBMISSION_PREFIX + uuid4().hex
        now = to_iso8601(utc_now())
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute(
                """
                INSERT INTO submissions (
                    id, user_id, problem_id, language, source_code,
                    status, result, score, total_time, created_at,
                    started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    submission_id,
                    teacher_id,
                    problem_id,
                    "python",
                    "print(3)",
                    "finished",
                    "AC",
                    100,
                    0.1,
                    now,
                    now,
                    now,
                ),
            )
            db.execute(
                """
                INSERT INTO judge_logs (
                    submission_id, case_id, result, score, time_used,
                    memory_used, exit_code, input_data, stdout, stderr,
                    expected_output, message, is_hidden, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    submission_id,
                    "case_01",
                    "AC",
                    100,
                    0.1,
                    None,
                    0,
                    "1 2\n",
                    "3\n",
                    "",
                    "3\n",
                    None,
                    0,
                    now,
                ),
            )
            db.commit()

        login_as(client, teacher_name)
        delete_response = client.delete(f"/api/problems/{problem_id}")
        assert delete_response.status_code == status.HTTP_200_OK
        assert delete_response.json()["data"] is None
        assert client.get(
            f"/api/problems/{problem_id}"
        ).status_code == status.HTTP_404_NOT_FOUND
        assert client.delete(
            f"/api/problems/{problem_id}"
        ).status_code == status.HTTP_404_NOT_FOUND

        with sqlite3.connect(DATABASE_PATH) as db:
            submissions_sql = db.execute(
                "SELECT sql FROM sqlite_master WHERE name = 'submissions'"
            ).fetchone()[0]
            assert "REFERENCES problems" not in submissions_sql
            assert db.execute(
                "SELECT COUNT(*) FROM test_cases WHERE problem_id = ?",
                (problem_id,),
            ).fetchone()[0] == 0
            assert db.execute(
                "SELECT COUNT(*) FROM submissions WHERE id = ?",
                (submission_id,),
            ).fetchone()[0] == 1
            assert db.execute(
                "SELECT COUNT(*) FROM judge_logs WHERE submission_id = ?",
                (submission_id,),
            ).fetchone()[0] == 1


def test_problem_pagination_defaults_bounds_and_shape() -> None:
    with TestClient(app) as client:
        create_problem_as_teacher(client)
        for _ in range(2):
            response = client.post(
                "/api/problems",
                json=make_problem(unique_problem_id()),
            )
            assert response.status_code == status.HTTP_201_CREATED

        student_name, _ = register_user(client, UserRole.STUDENT)
        login_as(client, student_name)
        response = client.get("/api/problems")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert {"items", "total", "page", "page_size"} == set(data)

        assert client.get(
            "/api/problems",
            params={"page": 0},
        ).status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert client.get(
            "/api/problems",
            params={"page_size": 0},
        ).status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert client.get(
            "/api/problems",
            params={"page_size": 101},
        ).status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
