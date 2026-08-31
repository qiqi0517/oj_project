from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.utils.response import success_response

router = APIRouter(
    prefix="/api",
    tags=["health"],
)

@router.get("/health")
async def health() -> JSONResponse:
    return success_response(
        data={
            "status": "running",
        }
    )
