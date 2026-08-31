from fastapi import APIRouter

router = APIRouter(
    prefix="/api/submissions",
    tags=["submissions"],
)