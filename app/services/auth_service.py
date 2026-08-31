from uuid import uuid4

import aiosqlite
from fastapi import status

from app.models.enums import UserRole
from app.models.user import UserPublic
from app.repositories.user_repository import (
    create_user,
    get_user_by_username,
)
from app.utils.exceptions import AppError
from app.utils.password import hash_password, verify_password
from app.utils.time import to_iso8601, utc_now

INVALID_CREDENTIALS_MESSAGE = "invalid username or password"


async def register_user(
    username: str,
    password: str,
) -> UserPublic:
    existing_user = await get_user_by_username(username)
    if existing_user is not None:
        raise AppError(status.HTTP_409_CONFLICT, "username already exists")

    user_id = str(uuid4())
    password_hash = hash_password(password)
    now = to_iso8601(utc_now())
    try:
        user = await create_user(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            role=UserRole.STUDENT,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
    except aiosqlite.IntegrityError:
        raise AppError(status.HTTP_409_CONFLICT, "username already exists")
    return UserPublic.model_validate(user)


async def authenticate_user(
    username: str,
    password: str,
) -> UserPublic:
    user = await get_user_by_username(username)
    if user is None:
        raise AppError(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS_MESSAGE)
    if not verify_password(password, user["password_hash"]):
        raise AppError(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS_MESSAGE)
    if not user["is_active"]:
        raise AppError(status.HTTP_403_FORBIDDEN, "user is disabled")
    return UserPublic.model_validate(user)
