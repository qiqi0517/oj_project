from fastapi import APIRouter

router = APIRouter(
    prefix="/api/problems",
    tags=["problems"],
)