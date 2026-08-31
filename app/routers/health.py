from fastapi import APIRouter

from app.utils.response import success_response

router = APIRouter(
    prefix="/api",
    tags=["health"],
)

@router.get("/health")
async def health():
    return success_response(
        data={
            "status": "running",
        }
    )