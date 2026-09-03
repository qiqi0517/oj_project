from typing import Any

from app.models.language import LanguageCreate
from app.repositories.database import get_db_connection


def _row_to_language(row: Any) -> dict[str, Any]:
    return {
        "name": row["name"],
        "file_ext": row["file_ext"],
        "compile_cmd": row["compile_cmd"],
        "run_cmd": row["run_cmd"],
        "time_limit": row["time_limit"],
        "memory_limit": row["memory_limit"],
    }


async def create_language(language: LanguageCreate) -> dict[str, Any]:
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO languages (
                name, file_ext, compile_cmd, run_cmd, time_limit, memory_limit
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                language.name,
                language.file_ext,
                language.compile_cmd,
                language.run_cmd,
                language.time_limit,
                language.memory_limit,
            ),
        )
        await db.commit()
    created = await get_language(language.name)
    if created is None:
        raise RuntimeError("failed to load created language")
    return created


async def get_language(name: str) -> dict[str, Any] | None:
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM languages WHERE name = ?",
            (name,),
        )
        row = await cursor.fetchone()
    return _row_to_language(row) if row else None


async def list_languages() -> list[dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM languages ORDER BY name")
        rows = await cursor.fetchall()
    return [_row_to_language(row) for row in rows]


async def ensure_language(language: LanguageCreate) -> None:
    if await get_language(language.name) is None:
        await create_language(language)
        return
    async with get_db_connection() as db:
        await db.execute(
            """
            UPDATE languages
            SET file_ext = ?, compile_cmd = ?, run_cmd = ?,
                time_limit = ?, memory_limit = ?
            WHERE name = ?
            """,
            (
                language.file_ext,
                language.compile_cmd,
                language.run_cmd,
                language.time_limit,
                language.memory_limit,
                language.name,
            ),
        )
        await db.commit()
