from uuid import uuid4

from app.config import (
    INITIAL_ADMIN_PASSWORD,
    INITIAL_ADMIN_USERNAME,
)
from app.models.enums import UserRole
from app.repositories.user_repository import (
    create_user,
    get_user_by_username,
)
from app.utils.password import hash_password
from app.utils.time import to_iso8601, utc_now


async def ensure_initial_admin() -> None:
    existing_user = await get_user_by_username(
        INITIAL_ADMIN_USERNAME
    )
    # if user exists, return
    if existing_user is not None:
        return
    # if not, create user
    now = to_iso8601(utc_now())
    await create_user(
        user_id=str(uuid4()),
        username=INITIAL_ADMIN_USERNAME,
        password_hash=hash_password(INITIAL_ADMIN_PASSWORD),
        role=UserRole.ADMIN.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )