import asyncio
import json
import sqlite3
import time
from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import DATABASE_PATH
from app.main import app
from app.models.enums import SubmissionStatus
from app.models.submission import (
    SubmissionCreateResponse,
    SubmissionListItem,
    SubmissionListResponse,
)
from app.services import submission_service
from app.utils.exceptions import AppError
from app.utils.response import success_response

TEST_PASSWORD = "secret1"


def test_submission_list_item_uses_null_for_unavailable_fields() -> None:
    created = SubmissionCreateResponse(
        submission_id="submission-1",
        status=SubmissionStatus.PENDING,
    )
    listed = SubmissionListResponse(
        total=1,
        submissions=[
            SubmissionListItem(
                submission_id=created.submission_id,
                status=created.status,
            )
        ],
    )

    body = json.loads(success_response(data=listed).body)

    assert body["data"] == {
        "total": 1,
        "submissions": [
            {
                "submission_id": "submission-1",
                "status": "pending",
                "score": None,
                "counts": None,
            }
        ],
    }


@pytest.fixture(autouse=True)
def cleanup_submission_data() -> Generator[None, None, None]:
    yield
    with sqlite3.connect(DATABASE_PATH) as db:
        submission_ids = [
            row[0]
            for row in db.execute(
                "SELECT id FROM submissions WHERE problem_id LIKE 'NEWSUB_%'"
            ).fetchall()
        ]
        for submission_id in submission_ids:
            db.execute(
                "DELETE FROM judge_logs WHERE submission_id = ?",
                (submission_id,),
            )
        db.execute("DELETE FROM submissions WHERE problem_id LIKE 'NEWSUB_%'")
        db.execute("DELETE FROM test_cases WHERE problem_id LIKE 'NEWSUB_%'")
        db.execute("DELETE FROM problems WHERE id LIKE 'NEWSUB_%'")
        db.execute("DELETE FROM users WHERE username LIKE 'testsubmission_%'")
        db.commit()


def register_login(client: TestClient) -> dict:
    username = f"testsubmission_{uuid4().hex[:8]}"
    registered = client.post(
        "/api/users/",
        json={"username": username, "password": TEST_PASSWORD},
    ).json()["data"]
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert response.status_code == status.HTTP_200_OK
    return registered


def login_admin(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admintestpassword"},
    )
    assert response.status_code == status.HTTP_200_OK


def create_problem(client: TestClient, testcase_count: int = 1) -> str:
    problem_id = f"NEWSUB_{uuid4().hex[:8]}"
    payload = {
        "id": problem_id,
        "title": "Submission Problem",
        "description": "Double the input.",
        "input_description": "One integer.",
        "output_description": "The doubled integer.",
        "samples": [{"input": "2\n", "output": "4\n"}],
        "constraints": "Small integers.",
        "testcases": [
            {"input": f"{number}\n", "output": f"{number * 2}\n"}
            for number in range(1, testcase_count + 1)
        ],
    }
    response = client.post("/api/problems/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    return problem_id


def submit(client: TestClient, problem_id: str, code: str) -> dict:
    response = client.post(
        "/api/submissions/",
        json={"problem_id": problem_id, "language": "python", "code": code},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "success"
    assert response.json()["data"]["status"] == "pending"
    return response.json()["data"]


def wait_for_result(client: TestClient, submission_id: str) -> dict:
    for _ in range(100):
        response = client.get(f"/api/submissions/{submission_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        if data["status"] != "pending":
            return data
        time.sleep(0.02)
    raise AssertionError("submission did not finish")


def test_create_submission_runs_in_background_and_updates_counts() -> None:
    with TestClient(app) as client:
        user = register_login(client)
        problem_id = create_problem(client, testcase_count=2)
        created = submit(
            client,
            problem_id,
            "print(int(input()) * 2)",
        )
        finished = wait_for_result(client, created["submission_id"])
        user_response = client.get(f"/api/users/{user['user_id']}")

    assert finished["status"] == "success"
    assert finished["score"] == 20
    assert finished["counts"] == 20
    assert set(finished) == {
        "submission_id",
        "status",
        "score",
        "counts",
        "compile_info",
        "run_info",
        "error_info",
    }
    assert finished["compile_info"] is None
    assert finished["run_info"] == {
        "result": "finished",
        "message": "2 test cases finished",
    }
    assert finished["error_info"] == ""
    assert user_response.json()["data"]["submit_count"] == 1
    assert user_response.json()["data"]["resolve_count"] == 1


def test_submission_ownership_and_admin_access() -> None:
    with TestClient(app) as owner_client, TestClient(app) as other_client:
        owner = register_login(owner_client)
        problem_id = create_problem(owner_client)
        created = submit(owner_client, problem_id, "print(int(input()) * 2)")
        wait_for_result(owner_client, created["submission_id"])
        register_login(other_client)
        denied = other_client.get(f"/api/submissions/{created['submission_id']}")
        other_client.post("/api/auth/logout")
        login_admin(other_client)
        allowed = other_client.get(f"/api/submissions/{created['submission_id']}")

    assert owner["role"] == "user"
    assert denied.status_code == status.HTTP_403_FORBIDDEN
    assert allowed.status_code == status.HTTP_200_OK


def test_submission_list_filters_pagination_and_permissions() -> None:
    with TestClient(app) as client:
        user = register_login(client)
        problem_id = create_problem(client)
        first = submit(client, problem_id, "print(int(input()) * 2)")
        second = submit(client, problem_id, "print(0)")
        wait_for_result(client, first["submission_id"])
        wait_for_result(client, second["submission_id"])
        missing_primary = client.get("/api/submissions/")
        invalid_page = client.get(f"/api/submissions/?user_id={user['user_id']}&page=1")
        page = client.get(f"/api/submissions/?problem_id={problem_id}&page_size=1")
        other_user = client.get(f"/api/submissions/?user_id={uuid4()}")

    assert missing_primary.status_code == status.HTTP_400_BAD_REQUEST
    assert invalid_page.status_code == status.HTTP_400_BAD_REQUEST
    assert page.status_code == status.HTTP_200_OK
    assert page.json()["data"]["total"] == 2
    assert len(page.json()["data"]["submissions"]) == 1
    assert other_user.status_code == status.HTTP_403_FORBIDDEN


def test_fourth_submission_in_one_minute_returns_429() -> None:
    with TestClient(app) as client:
        register_login(client)
        problem_id = create_problem(client)
        responses = [
            client.post(
                "/api/submissions/",
                json={
                    "problem_id": problem_id,
                    "language": "python",
                    "code": "print(2)",
                },
            )
            for _ in range(4)
        ]

    assert [response.status_code for response in responses[:3]] == [200, 200, 200]
    assert responses[3].status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_only_admin_can_rejudge_and_submission_id_is_reused() -> None:
    with TestClient(app) as client:
        register_login(client)
        problem_id = create_problem(client)
        created = submit(client, problem_id, "print(0)")
        wait_for_result(client, created["submission_id"])
        denied = client.put(f"/api/submissions/{created['submission_id']}/rejudge")
        client.post("/api/auth/logout")
        login_admin(client)
        accepted = client.put(f"/api/submissions/{created['submission_id']}/rejudge")
        detail = client.get(f"/api/submissions/{created['submission_id']}")

    assert denied.status_code == status.HTTP_403_FORBIDDEN
    assert accepted.status_code == status.HTTP_200_OK
    assert accepted.json()["msg"] == "rejudge started"
    assert accepted.json()["data"] == {
        "submission_id": created["submission_id"],
        "status": "pending",
    }
    assert detail.status_code == status.HTTP_200_OK


def test_pending_submission_cannot_be_rejudged(monkeypatch) -> None:
    started_submission_ids: list[str] = []
    monkeypatch.setattr(
        submission_service,
        "start_judge_task",
        started_submission_ids.append,
    )

    with TestClient(app) as client:
        register_login(client)
        problem_id = create_problem(client)
        created = submit(client, problem_id, "print(int(input()) * 2)")
        client.post("/api/auth/logout")
        login_admin(client)
        response = client.put(
            f"/api/submissions/{created['submission_id']}/rejudge"
        )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["code"] == status.HTTP_409_CONFLICT
    assert started_submission_ids == [created["submission_id"]]


def test_concurrent_rejudge_only_starts_one_task(monkeypatch) -> None:
    with TestClient(app) as client:
        register_login(client)
        problem_id = create_problem(client)
        created = submit(client, problem_id, "print(int(input()) * 2)")
        wait_for_result(client, created["submission_id"])

        started_submission_ids: list[str] = []
        monkeypatch.setattr(
            submission_service,
            "start_judge_task",
            started_submission_ids.append,
        )

        async def call_rejudge() -> str | int:
            try:
                result = await submission_service.rejudge_submission(
                    created["submission_id"]
                )
                return result.status.value
            except AppError as exc:
                return exc.status_code

        async def rejudge_twice() -> list[str | int]:
            return await asyncio.gather(call_rejudge(), call_rejudge())

        results = asyncio.run(rejudge_twice())

    assert results.count(SubmissionStatus.PENDING.value) == 1
    assert results.count(status.HTTP_409_CONFLICT) == 1
    assert started_submission_ids == [created["submission_id"]]


def test_rejudge_updates_resolve_count_and_replaces_logs() -> None:
    with TestClient(app) as client:
        user = register_login(client)
        problem_id = create_problem(client, testcase_count=2)
        created = submit(client, problem_id, "print(int(input()) * 2)")
        wait_for_result(client, created["submission_id"])
        client.post("/api/auth/logout")
        login_admin(client)

        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute(
                "UPDATE submissions SET source_code = 'print(0)' WHERE id = ?",
                (created["submission_id"],),
            )
            db.commit()

        first_rejudge = client.put(
            f"/api/submissions/{created['submission_id']}/rejudge"
        )
        wrong_result = wait_for_result(client, created["submission_id"])
        after_wrong = client.get(f"/api/users/{user['user_id']}").json()["data"]

        with sqlite3.connect(DATABASE_PATH) as db:
            wrong_logs = db.execute(
                "SELECT result FROM judge_logs WHERE submission_id = ? ORDER BY id",
                (created["submission_id"],),
            ).fetchall()
            db.execute(
                """
                UPDATE submissions
                SET source_code = 'print(int(input()) * 2)'
                WHERE id = ?
                """,
                (created["submission_id"],),
            )
            db.commit()

        second_rejudge = client.put(
            f"/api/submissions/{created['submission_id']}/rejudge"
        )
        accepted_result = wait_for_result(client, created["submission_id"])
        after_accepted = client.get(f"/api/users/{user['user_id']}").json()["data"]

        with sqlite3.connect(DATABASE_PATH) as db:
            accepted_logs = db.execute(
                "SELECT result FROM judge_logs WHERE submission_id = ? ORDER BY id",
                (created["submission_id"],),
            ).fetchall()

    assert first_rejudge.status_code == status.HTTP_200_OK
    assert wrong_result["score"] == 0
    assert after_wrong["resolve_count"] == 0
    assert wrong_logs == [("WA",), ("WA",)]
    assert second_rejudge.status_code == status.HTTP_200_OK
    assert accepted_result["score"] == accepted_result["counts"] == 20
    assert after_accepted["resolve_count"] == 1
    assert accepted_logs == [("AC",), ("AC",)]


def test_rejudge_system_error_revokes_sole_accepted_problem(
    monkeypatch,
) -> None:
    with TestClient(app) as client:
        user = register_login(client)
        problem_id = create_problem(client)
        created = submit(client, problem_id, "print(int(input()) * 2)")
        wait_for_result(client, created["submission_id"])
        client.post("/api/auth/logout")
        login_admin(client)

        async def fail_evaluation(*args, **kwargs):
            raise RuntimeError("forced judge failure")

        monkeypatch.setattr(
            submission_service,
            "evaluate_language",
            fail_evaluation,
        )
        response = client.put(
            f"/api/submissions/{created['submission_id']}/rejudge"
        )
        failed_result = wait_for_result(client, created["submission_id"])
        user_data = client.get(f"/api/users/{user['user_id']}").json()["data"]

    with sqlite3.connect(DATABASE_PATH) as db:
        stored = db.execute(
            "SELECT result, score, counts FROM submissions WHERE id = ?",
            (created["submission_id"],),
        ).fetchone()

    assert response.status_code == status.HTTP_200_OK
    assert failed_result["status"] == SubmissionStatus.ERROR.value
    assert failed_result["error_info"] == "judge internal error"
    assert user_data["resolve_count"] == 0
    assert stored == (None, 0, 0)


def test_rejudge_system_error_keeps_count_when_another_submission_is_ac(
    monkeypatch,
) -> None:
    with TestClient(app) as client:
        user = register_login(client)
        problem_id = create_problem(client)
        first = submit(client, problem_id, "print(int(input()) * 2)")
        second = submit(client, problem_id, "print(int(input()) * 2)")
        wait_for_result(client, first["submission_id"])
        wait_for_result(client, second["submission_id"])
        client.post("/api/auth/logout")
        login_admin(client)

        async def fail_evaluation(*args, **kwargs):
            raise RuntimeError("forced judge failure")

        monkeypatch.setattr(
            submission_service,
            "evaluate_language",
            fail_evaluation,
        )
        client.put(f"/api/submissions/{first['submission_id']}/rejudge")
        failed_result = wait_for_result(client, first["submission_id"])
        user_data = client.get(f"/api/users/{user['user_id']}").json()["data"]

    assert failed_result["status"] == SubmissionStatus.ERROR.value
    assert user_data["resolve_count"] == 1
