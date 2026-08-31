from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.models.user import (
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
)
from app.utils.auth import get_current_user
from app.utils.response import success_response


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request_data: UserRegisterRequest,
) -> JSONResponse:
    user = await register_user(
        username=request_data.username,
        password=request_data.password,
    )
    return success_response(
        data=user,
        message="user registered",
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login")
async def login(
    request_data: UserLoginRequest,
    request: Request,
) -> JSONResponse:
    user = await authenticate_user(
        username=request_data.username,
        password=request_data.password,
    )
    request.session["user_id"] = user.id
    return success_response(
        data=user,
        message="login successful",
    )


@router.get("/me")
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    public_user = UserPublic.model_validate(current_user)
    return success_response(
        data=public_user,
    )


@router.post("/logout")
async def logout(
    request: Request,
) -> JSONResponse:
    request.session.clear()
    return success_response(
        data=None,
        message="logout successful",
    )