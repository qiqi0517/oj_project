import sqlite3
import time
from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import DATABASE_PATH
from app.main import app

TEST_PASSWORD = "secret1"


@pytest.fixture(autouse=True)
def cleanup_log_data() -> Generator[None, None, None]:
    yield
    with sqlite3.connect(DATABASE_PATH) as db:
        db.execute("DELETE FROM access_logs WHERE problem_id LIKE 'NEWLOG_%'")
        submission_ids = [
            row[0]
            for row in db.execute(
                "SELECT id FROM submissions WHERE problem_id LIKE 'NEWLOG_%'"
            ).fetchall()
        ]
        for submission_id in submission_ids:
            db.execute(
                "DELETE FROM judge_logs WHERE submission_id = ?",
                (submission_id,),
            )
        db.execute("DELETE FROM submissions WHERE problem_id LIKE 'NEWLOG_%'")
        db.execute("DELETE FROM test_cases WHERE problem_id LIKE 'NEWLOG_%'")
        db.execute("DELETE FROM problems WHERE id LIKE 'NEWLOG_%'")
        db.execute("DELETE FROM users WHERE username LIKE 'testlog_%'")
        db.commit()


def register_login(client: TestClient) -> dict:
    username = f"testlog_{uuid4().hex[:8]}"
    user = client.post(
        "/api/users/",
        json={"username": username, "password": TEST_PASSWORD},
    ).json()["data"]
    client.post(
        "/api/auth/login",
        json={"username": username, "password": TEST_PASSWORD},
    )
    return user


def login_admin(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admintestpassword"},
    )
    assert response.status_code == status.HTTP_200_OK


def create_problem_and_submission(client: TestClient) -> tuple[str, str]:
    problem_id = f"NEWLOG_{uuid4().hex[:8]}"
    client.post(
        "/api/problems/",
        json={
            "id": problem_id,
            "title": "Log Problem",
            "description": "Echo input.",
            "input_description": "Text.",
            "output_description": "Same text.",
            "samples": [{"input": "hello\n", "output": "hello\n"}],
            "constraints": "Short text.",
            "testcases": [
                {"input": "hello\n", "output": "hello\n"},
                {"input": "world\n", "output": "world\n"},
            ],
        },
    )
    response = client.post(
        "/api/submissions/",
        json={
            "problem_id": problem_id,
            "language": "python",
            "code": "print(input())",
        },
    )
    submission_id = response.json()["data"]["submission_id"]
    for _ in range(100):
        detail = client.get(f"/api/submissions/{submission_id}")
        if detail.json()["data"]["status"] != "pending":
            break
        time.sleep(0.02)
    return problem_id, submission_id


def test_owner_log_contains_only_public_testcase_detail_fields() -> None:
    with TestClient(app) as client:
        register_login(client)
        _, submission_id = create_problem_and_submission(client)
        response = client.get(f"/api/submissions/{submission_id}/log")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["score"] == 20
    assert data["counts"] == 20
    assert len(data["details"]) == 2
    assert set(data["details"][0]) == {"id", "result", "time", "memory"}
    assert "stdout" not in response.text
    assert str(DATABASE_PATH) not in response.text


def test_denied_log_access_records_403_but_missing_submission_does_not() -> None:
    with TestClient(app) as owner_client, TestClient(app) as other_client:
        register_login(owner_client)
        problem_id, submission_id = create_problem_and_submission(owner_client)
        other = register_login(other_client)
        denied = other_client.get(f"/api/submissions/{submission_id}/log")
        missing = other_client.get(f"/api/submissions/{uuid4()}/log")

    assert denied.status_code == status.HTTP_403_FORBIDDEN
    assert missing.status_code == status.HTTP_404_NOT_FOUND
    with sqlite3.connect(DATABASE_PATH) as db:
        rows = db.execute(
            """
            SELECT status FROM access_logs
            WHERE user_id = ? AND problem_id = ?
            """,
            (other["user_id"], problem_id),
        ).fetchall()
    assert rows == [(403,)]


def test_public_cases_allows_log_but_not_submission_summary() -> None:
    with TestClient(app) as owner_client, TestClient(app) as viewer_client:
        register_login(owner_client)
        problem_id, submission_id = create_problem_and_submission(owner_client)
        owner_client.post("/api/auth/logout")
        login_admin(owner_client)
        visibility = owner_client.put(
            f"/api/problems/{problem_id}/log_visibility",
            json={"public_cases": True},
        )
        register_login(viewer_client)
        log_response = viewer_client.get(f"/api/submissions/{submission_id}/log")
        summary_response = viewer_client.get(f"/api/submissions/{submission_id}")

    assert visibility.status_code == status.HTTP_200_OK
    assert log_response.status_code == status.HTTP_200_OK
    assert summary_response.status_code == status.HTTP_403_FORBIDDEN


def test_only_admin_can_query_filtered_access_logs() -> None:
    with TestClient(app) as owner_client, TestClient(app) as admin_client:
        owner = register_login(owner_client)
        problem_id, submission_id = create_problem_and_submission(owner_client)
        owner_client.get(f"/api/submissions/{submission_id}/log")
        denied = owner_client.get("/api/logs/access/")
        login_admin(admin_client)
        response = admin_client.get(
            f"/api/logs/access/?user_id={owner['user_id']}&problem_id={problem_id}"
            "&page_size=1"
        )
        invalid_page = admin_client.get("/api/logs/access/?page=1")

    assert denied.status_code == status.HTTP_403_FORBIDDEN
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["data"]) == 1
    log = response.json()["data"][0]
    assert set(log) >= {"user_id", "problem_id", "action", "time", "status"}
    assert log["action"] == "view_logs"
    assert log["status"] == "200"
    assert invalid_page.status_code == status.HTTP_400_BAD_REQUEST
