from fastapi import status

from app.models.log import AccessLogResponse
from app.repositories import log_repository
from app.utils.exceptions import AppError


async def get_access_logs(
    *,
    user_id: str | None,
    problem_id: str | None,
    page: int | None,
    page_size: int | None,
) -> list[AccessLogResponse]:
    if page is not None and page_size is None:
        raise AppError(status.HTTP_400_BAD_REQUEST, "page_size is required")
    logs = await log_repository.list_access_logs(
        user_id=user_id,
        problem_id=problem_id,
        page=page,
        page_size=page_size,
    )
    return [AccessLogResponse.model_validate(log) for log in logs]
