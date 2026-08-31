from typing import Any

from app.repositories.database import get_db_connection


async def get_user_by_username(username: str) -> dict[str, Any] | None:
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_user(
    *,
    user_id: str,
    username: str,
    password_hash: str,
    role: str,
    is_active: bool,
    created_at: str,
    updated_at: str,
) -> None:
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO users (
                id,
                username,
                password_hash,
                role,
                is_active,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                password_hash,
                role,
                int(is_active),
                created_at,
                updated_at,
            ),
        )
        await db.commit()