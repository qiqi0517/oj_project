from uuid import uuid4

from app.models.enums import UserRole
from app.repositories.user_repository import (
    create_user,
    get_user_by_username,
)
from app.utils.password import hash_password
from app.utils.time import to_iso8601, utc_now

TEST_PASSWORD = "password123"


async def ensure_test_user(
    username: str,
    role: UserRole,
    is_active: bool = True,
) -> None:
    existing_user = await get_user_by_username(username)
    if existing_user is not None:
        return
    now = to_iso8601(utc_now())
    await create_user(
        user_id=str(uuid4()),
        username=username,
        password_hash=hash_password(TEST_PASSWORD),
        role=role,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )

async def prepare_test_users() -> None:
    await ensure_test_user(
        username="student01",
        role=UserRole.STUDENT,
    )
    await ensure_test_user(
        username="teacher01",
        role=UserRole.TEACHER,
    )
    await ensure_test_user(
        username="disabled01",
        role=UserRole.STUDENT,
        is_active=False,
    )