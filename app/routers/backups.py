from fastapi import APIRouter

router = APIRouter(
    prefix="/api/admin/backups",
    tags=["backups"],
)