from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.models.log import AccessLogResponse
from app.models.response import ApiResponse
from app.services import log_service
from app.utils.auth import require_admin
from app.utils.response import success_response


router = APIRouter(
    prefix="/api/logs",
    tags=["logs"],
)


@router.get(
    "/access/",
    response_model=ApiResponse[list[AccessLogResponse]],
)
async def get_access_logs(
    user_id: str | None = None,
    problem_id: str | None = None,
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1),
    _current_user: dict[str, Any] = Depends(require_admin),
) -> JSONResponse:
    data = await log_service.get_access_logs(
        user_id=user_id,
        problem_id=problem_id,
        page=page,
        page_size=page_size,
    )
    return success_response(data=data)
