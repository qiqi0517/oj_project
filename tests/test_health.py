from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["code"] == status.HTTP_200_OK
        assert body["data"]["status"] == "running"
