from typing import Any

from fastapi import Depends, Request, status

from app.models.enums import UserRole
from app.repositories.user_repository import get_user_by_id
from app.utils.exceptions import AppError


async def get_current_user(request: Request) -> dict[str, Any]:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "not authenticated")

    user = await get_user_by_id(user_id)
    if user is None:
        request.session.clear()
        raise AppError(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    if user["role"] == UserRole.BANNED.value:
        raise AppError(status.HTTP_403_FORBIDDEN, "user is banned")

    return user


async def require_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if current_user["role"] != UserRole.ADMIN.value:
        raise AppError(status.HTTP_403_FORBIDDEN, "permission denied")
    return current_user
