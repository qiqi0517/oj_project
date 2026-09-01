from app.models.health import HealthResponse


def get_health() -> HealthResponse:
    return HealthResponse.model_validate({"status": "running"})
