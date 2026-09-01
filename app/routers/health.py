from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.health import HealthResponse
from app.models.response import ApiResponse
from app.services.health_service import get_health
from app.utils.response import success_response

router = APIRouter(
    prefix="/api",
    tags=["health"],
)

@router.get("/health", response_model=ApiResponse[HealthResponse])
async def health() -> JSONResponse:
    return success_response(data=get_health())
