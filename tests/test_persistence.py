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


@pytest.mark.skip(reason="backup creation is not implemented yet")
def test_create_backup() -> None:
    """An admin should be able to create a database backup."""


@pytest.mark.skip(reason="backup restore is not implemented yet")
def test_restore_backup() -> None:
    """A valid backup should restore persisted data."""


@pytest.mark.skip(reason="backup restore is not implemented yet")
def test_corrupt_backup_does_not_damage_current_data() -> None:
    """A corrupt backup should fail without changing current data."""
