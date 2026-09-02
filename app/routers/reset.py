from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.config import TESTING
from app.models.response import ApiResponse
from app.repositories.database import reset_database
from app.services.user_service import ensure_initial_admin
from app.services.language_service import ensure_default_languages
from app.utils.auth import get_current_user, require_admin
from app.utils.response import success_response


router = APIRouter(
    prefix="/api",
    tags=["test reset"],
)


async def require_reset_access(request: Request) -> dict[str, Any] | None:
    if TESTING:
        return None
    return await require_admin(await get_current_user(request))


@router.post("/reset/", response_model=ApiResponse[None])
async def reset_system(
    request: Request,
    _current_user: dict[str, Any] | None = Depends(require_reset_access),
) -> JSONResponse:
    await reset_database()
    await ensure_initial_admin()
    await ensure_default_languages()
    request.session.clear()
    return success_response(data=None, msg="system reset successfully")
