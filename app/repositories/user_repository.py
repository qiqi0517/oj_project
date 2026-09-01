import json
from typing import Any

import aiosqlite

from app.repositories.database import get_db_connection


def _row_to_user(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "password_hash": row["password_hash"],
        "role": row["role"],
        "submit_count": row["submit_count"],
        "resolve_count": row["resolve_count"],
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
                submit_count,
                resolve_count,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (
                user_id,
                username,
                password_hash,
                role,
                created_at,
                updated_at,
            ),
        )
        await db.commit()
    user = await get_user_by_id(user_id)
    if user is None:
        raise RuntimeError("failed to load created user")
    return user


async def update_initial_admin(
    user_id: str,
    password_hash: str,
    updated_at: str,
) -> None:
    async with get_db_connection() as db:
        await db.execute(
            """
            UPDATE users
            SET password_hash = ?, role = 'admin', updated_at = ?
            WHERE id = ?
            """,
            (password_hash, updated_at, user_id),
        )
        await db.commit()


async def list_users(
    page: int | None,
    page_size: int | None,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM users ORDER BY created_at, id"
    parameters: tuple[int, ...] = ()
    if page_size is not None:
        offset = ((page or 1) - 1) * page_size
        query += " LIMIT ? OFFSET ?"
        parameters = (page_size, offset)
    async with get_db_connection() as db:
        cursor = await db.execute(query, parameters)
        rows = await cursor.fetchall()
    return [_row_to_user(row) for row in rows]


async def count_users() -> int:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
    return int(row[0]) if row is not None else 0


async def update_user_role(
    user_id: str,
    role: str,
    updated_at: str,
) -> dict[str, Any] | None:
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            UPDATE users
            SET role = ?, updated_at = ?
            WHERE id = ?
            """,
            (role, updated_at, user_id),
        )
        await db.commit()
    if cursor.rowcount == 0:
        return None
    return await get_user_by_id(user_id)


async def create_role_audit_log(
    *,
    log_id: str,
    operator_id: str,
    target_id: str,
    role: str,
    created_at: str,
) -> None:
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO audit_logs (
                id, operator_id, action, target_type, target_id,
                success, detail, created_at
            )
            VALUES (?, ?, 'UPDATE_USER_ROLE', 'user', ?, 1, ?, ?)
            """,
            (
                log_id,
                operator_id,
                target_id,
                json.dumps({"role": role}),
                created_at,
            ),
        )
        await db.commit()
