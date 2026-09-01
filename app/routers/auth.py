from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.models.user import (
    UserLoginRequest,
    UserLoginResponse,
    UserPublic,
)
from app.models.response import ApiResponse
from app.services.user_service import to_user_public, authenticate_user
from app.utils.auth import get_current_user
from app.utils.response import success_response


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


@router.post("/login", response_model=ApiResponse[UserLoginResponse])
async def login(
    request_data: UserLoginRequest,
    request: Request,
) -> JSONResponse:
    user = await authenticate_user(
        username=request_data.username,
        password=request_data.password,
    )
    request.session["user_id"] = user.user_id
    return success_response(
        data=user,
        msg="login success",
    )


@router.post("/logout", response_model=ApiResponse[None])
async def logout(
    request: Request,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    request.session.clear()
    return success_response(
        data=None,
        msg="logout success",
    )