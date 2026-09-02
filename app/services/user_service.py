from typing import Any
from uuid import uuid4

import aiosqlite
from fastapi import status

from app.config import INITIAL_ADMIN_PASSWORD, INITIAL_ADMIN_USERNAME
from app.models.enums import UserRole
from app.models.user import (
    UserCreateAdminResponse,
    UserListResponse,
    UserLoginResponse,
    UserPublic,
    UserRoleUpdateResponse,
)
from app.repositories.user_repository import (
    count_users,
    create_role_audit_log,
    create_user,
    get_user_by_id,
    get_user_by_username,
    list_users,
    update_initial_admin,
    update_user_role,
)
from app.utils.exceptions import AppError
from app.utils.password import hash_password, verify_password
from app.utils.time import to_iso8601, utc_now

INVALID_CREDENTIALS_MSG = "invalid username or password"


def to_user_public(user: dict[str, Any]) -> UserPublic:
    return UserPublic.model_validate(
        {
            "user_id": user["id"],
            "username": user["username"],
            "join_time": user["created_at"][:10],
            "role": user["role"],
            "submit_count": user["submit_count"],
            "resolve_count": user["resolve_count"],
        }
    )


def to_login_response(user: dict[str, Any]) -> UserLoginResponse:
    return UserLoginResponse.model_validate(
        {
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
    )


async def register_user(
    username: str,
    password: str,
) -> UserPublic:
    return await create_user_account(username, password)


async def authenticate_user(
    username: str,
    password: str,
) -> UserLoginResponse:
    user = await get_user_by_username(username)
    if user is None or not verify_password(password, user["password_hash"]):
        raise AppError(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS_MSG)
    if user["role"] == UserRole.BANNED.value:
        raise AppError(status.HTTP_403_FORBIDDEN, "user is banned")
    return to_login_response(user)


async def create_user_account(
    username: str,
    password: str,
    role: UserRole = UserRole.USER,
) -> UserPublic:
    if await get_user_by_username(username) is not None:
        raise AppError(status.HTTP_400_BAD_REQUEST, "username already exists")

    now = to_iso8601(utc_now())
    try:
        user = await create_user(
            user_id=str(uuid4()),
            username=username,
            password_hash=hash_password(password),
            role=role.value,
            created_at=now,
            updated_at=now,
        )
    except aiosqlite.IntegrityError as exc:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "username already exists",
        ) from exc
    return to_user_public(user)


async def create_admin_account(
    username: str,
    password: str,
) -> UserCreateAdminResponse:
    user = await create_user_account(
        username=username,
        password=password,
        role=UserRole.ADMIN,
    )
    return UserCreateAdminResponse.model_validate(
        {"user_id": user.user_id, "username": user.username}
    )


async def ensure_initial_admin() -> None:
    existing_user = await get_user_by_username(INITIAL_ADMIN_USERNAME)
    now = to_iso8601(utc_now())
    if existing_user is None:
        await create_user(
            user_id=str(uuid4()),
            username=INITIAL_ADMIN_USERNAME,
            password_hash=hash_password(INITIAL_ADMIN_PASSWORD),
            role=UserRole.ADMIN.value,
            created_at=now,
            updated_at=now,
        )
        return

    if existing_user["role"] != UserRole.ADMIN.value or not verify_password(
        INITIAL_ADMIN_PASSWORD,
        existing_user["password_hash"],
    ):
        await update_initial_admin(
            existing_user["id"],
            hash_password(INITIAL_ADMIN_PASSWORD),
            now,
        )


async def get_user_public(
    user_id: str,
    current_user: dict[str, Any],
) -> UserPublic:
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise AppError(status.HTTP_403_FORBIDDEN, "permission denied")
    user = await get_user_by_id(user_id)
    if user is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "user not found")
    return to_user_public(user)


async def list_user_publics(
    page: int | None,
    page_size: int | None,
) -> UserListResponse:
    if page is not None and page_size is None:
        raise AppError(status.HTTP_400_BAD_REQUEST, "page_size is required")
    rows = await list_users(page, page_size)
    return UserListResponse.model_validate(
        {
            "total": await count_users(),
            "users": [to_user_public(row) for row in rows],
        }
    )


async def change_user_role(
    user_id: str,
    role: UserRole,
    operator_id: str,
) -> UserRoleUpdateResponse:
    now = to_iso8601(utc_now())
    user = await update_user_role(user_id, role.value, now)
    if user is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "user not found")
    await create_role_audit_log(
        log_id=str(uuid4()),
        operator_id=operator_id,
        target_id=user_id,
        role=role.value,
        created_at=now,
    )
    return UserRoleUpdateResponse.model_validate(
        {"user_id": user["id"], "role": user["role"]}
    )
