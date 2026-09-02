from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.models.response import ApiResponse
from app.models.user import (
    UserCreateAdminResponse,
    UserListResponse,
    UserPublic,
    UserRegisterRequest,
    UserRoleUpdateRequest,
    UserRoleUpdateResponse,
)
from app.services.user_service import (
    change_user_role,
    create_admin_account,
    get_user_public,
    list_user_publics,
    register_user,
)
from app.utils.auth import get_current_user, require_admin
from app.utils.response import success_response

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)


@router.post("/", response_model=ApiResponse[UserPublic])
async def register(
    request_data: UserRegisterRequest,
) -> JSONResponse:
    user = await register_user(
        username=request_data.username,
        password=request_data.password,
    )
    return success_response(data=user, msg="register success")


@router.post("/admin", response_model=ApiResponse[UserCreateAdminResponse])
async def create_admin(
    request_data: UserRegisterRequest,
    _current_user: dict[str, Any] = Depends(require_admin),
) -> JSONResponse:
    data = await create_admin_account(
        username=request_data.username,
        password=request_data.password,
    )
    return success_response(data=data)


@router.get("/", response_model=ApiResponse[UserListResponse])
async def get_users(
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1),
    _current_user: dict[str, Any] = Depends(require_admin),
) -> JSONResponse:
    data = await list_user_publics(page, page_size)
    return success_response(data=data)


@router.get("/{user_id}", response_model=ApiResponse[UserPublic])
async def get_user(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    user = await get_user_public(user_id, current_user)
    return success_response(data=user)


@router.put(
    "/{user_id}/role",
    response_model=ApiResponse[UserRoleUpdateResponse],
)
async def update_role(
    user_id: str,
    request_data: UserRoleUpdateRequest,
    current_user: dict[str, Any] = Depends(require_admin),
) -> JSONResponse:
    data = await change_user_role(
        user_id=user_id,
        role=request_data.role,
        operator_id=current_user["id"],
    )
    return success_response(
        data=data,
        msg="role updated",
    )
