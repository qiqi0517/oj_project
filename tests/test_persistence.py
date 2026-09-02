import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import database
from app.routers import reset as reset_router

TEST_PASSWORD = "secret1"


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch) -> Path:
    database_path = tmp_path / "oj-test.db"
    monkeypatch.setattr(database, "DATABASE_PATH", database_path)
    return database_path


def register(client: TestClient, username: str) -> dict:
    response = client.post(
        "/api/users/",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["data"]


def login(client: TestClient, username: str, password: str = TEST_PASSWORD) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == status.HTTP_200_OK


def make_problem() -> dict:
    return {
        "id": f"PERSIST_{uuid4().hex[:8]}",
        "title": "Persistent Problem",
        "description": "Persistent description.",
        "input_description": "Persistent input.",
        "output_description": "Persistent output.",
        "samples": [{"input": "1 2\n", "output": "3\n"}],
        "constraints": "None.",
        "testcases": [{"input": "1 2\n", "output": "3\n"}],
    }


def test_user_data_survives_application_restart() -> None:
    username = f"persistence_{uuid4().hex[:8]}"
    with TestClient(app) as client:
        user = register(client, username)

    with TestClient(app) as client:
        login(client, username)
        response = client.get(f"/api/users/{user['user_id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["username"] == username


def test_problem_and_testcases_survive_application_restart() -> None:
    username = f"persistence_{uuid4().hex[:8]}"
    problem = make_problem()
    with TestClient(app) as client:
        register(client, username)
        login(client, username)
        create_response = client.post("/api/problems/", json=problem)
        assert create_response.status_code == status.HTTP_200_OK

    with TestClient(app) as client:
        login(client, username)
        response = client.get(f"/api/problems/{problem['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["testcases"] == problem["testcases"]


def test_reset_clears_data_logs_out_and_recreates_admin(
    isolated_database: Path,
    monkeypatch,
) -> None:
    username = f"persistence_{uuid4().hex[:8]}"
    problem = make_problem()
    with TestClient(app) as client:
        register(client, username)
        login(client, username)
        client.post("/api/problems/", json=problem)
        denied_reset = client.post("/api/reset/")
        monkeypatch.setattr(reset_router, "TESTING", True)
        reset_response = client.post("/api/reset/")
        old_session_response = client.get("/api/users/")
        old_user_login = client.post(
            "/api/auth/login",
            json={"username": username, "password": TEST_PASSWORD},
        )
        admin_login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admintestpassword"},
        )

    assert denied_reset.status_code == status.HTTP_403_FORBIDDEN
    assert reset_response.status_code == status.HTTP_200_OK
    assert reset_response.json()["msg"] == "system reset successfully"
    assert reset_response.json()["data"] is None
    assert old_session_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert old_user_login.status_code == status.HTTP_401_UNAUTHORIZED
    assert admin_login.status_code == status.HTTP_200_OK

    with sqlite3.connect(isolated_database) as db:
        assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM problems").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 0
