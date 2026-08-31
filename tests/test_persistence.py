import sqlite3
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import DATABASE_PATH
from app.main import app


TEST_PASSWORD = "password123"


def test_user_data_survives_application_restart() -> None:
    username = f"persistence_{uuid4().hex[:8]}"
    try:
        with TestClient(app) as client:
            health_response = client.get("/api/health")
            assert health_response.status_code == status.HTTP_200_OK
            register_response = client.post(
                "/api/auth/register",
                json={
                    "username": username,
                    "password": TEST_PASSWORD,
                },
            )
            assert register_response.status_code == status.HTTP_201_CREATED

        with TestClient(app) as client:
            login_response = client.post(
                "/api/auth/login",
                json={
                    "username": username,
                    "password": TEST_PASSWORD,
                },
            )
            assert login_response.status_code == status.HTTP_200_OK
            me_response = client.get("/api/auth/me")
            assert me_response.status_code == status.HTTP_200_OK
            assert me_response.json()["data"]["username"] == username
    finally:
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute("DELETE FROM users WHERE username = ?", (username,))
            db.commit()


def test_problem_and_test_cases_survive_application_restart() -> None:
    username = f"persistence_{uuid4().hex[:8]}"
    problem_id = f"PERSIST_{uuid4().hex[:8]}"
    problem = {
        "id": problem_id,
        "title": "Persistent Problem",
        "description": "Persistent description.",
        "input_description": "Persistent input.",
        "output_description": "Persistent output.",
        "samples": [{"input": "1 2\n", "output": "3\n"}],
        "constraints": "None.",
        "time_limit": 1.0,
        "memory_limit": 128,
        "difficulty": "easy",
        "tags": ["persistence"],
        "test_cases": [
            {
                "case_id": "case_01",
                "input": "1 2\n",
                "output": "3\n",
                "score": 100,
                "is_hidden": True,
            }
        ],
    }
    try:
        with TestClient(app) as client:
            register_response = client.post(
                "/api/auth/register",
                json={"username": username, "password": TEST_PASSWORD},
            )
            user_id = register_response.json()["data"]["id"]
            with sqlite3.connect(DATABASE_PATH) as db:
                db.execute(
                    "UPDATE users SET role = 'teacher' WHERE id = ?",
                    (user_id,),
                )
                db.commit()
            client.post(
                "/api/auth/login",
                json={"username": username, "password": TEST_PASSWORD},
            )
            create_response = client.post("/api/problems", json=problem)
            assert create_response.status_code == status.HTTP_201_CREATED

        with TestClient(app) as client:
            login_response = client.post(
                "/api/auth/login",
                json={"username": username, "password": TEST_PASSWORD},
            )
            assert login_response.status_code == status.HTTP_200_OK
            detail_response = client.get(f"/api/problems/{problem_id}")
            assert detail_response.status_code == status.HTTP_200_OK
            assert detail_response.json()["data"]["id"] == problem_id
            assert len(detail_response.json()["data"]["test_cases"]) == 1
    finally:
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute("DELETE FROM test_cases WHERE problem_id = ?", (problem_id,))
            db.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
            db.execute("DELETE FROM users WHERE username = ?", (username,))
            db.commit()


@pytest.mark.skip(reason="backup creation is not implemented yet")
def test_create_backup() -> None:
    """An admin should be able to create a database backup."""


@pytest.mark.skip(reason="backup restore is not implemented yet")
def test_restore_backup() -> None:
    """A valid backup should restore persisted data."""


@pytest.mark.skip(reason="backup restore is not implemented yet")
def test_corrupt_backup_does_not_damage_current_data() -> None:
    """A corrupt backup should fail without changing current data."""
