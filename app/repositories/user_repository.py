from typing import Any

import aiosqlite

from app.repositories.database import get_db_connection


def _row_to_user(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "password_hash": row["password_hash"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }

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
    return _row_to_user(row) if row else None


async def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
    return _row_to_user(row) if row else None


async def create_user(
    *,
    user_id: str,
    username: str,
    password_hash: str,
    role: str,
    is_active: bool,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
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
    user = await get_user_by_id(user_id)
    if user is None:
        raise RuntimeError("failed to load created user")
    return user
