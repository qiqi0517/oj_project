from typing import Any

from app.repositories.database import get_db_connection


async def create_access_log(
    *,
    user_id: str,
    problem_id: str,
    action: str,
    access_time: str,
    access_status: int,
) -> None:
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO access_logs (user_id, problem_id, action, time, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, problem_id, action, access_time, access_status),
        )
        await db.commit()


async def list_access_logs(
    *,
    user_id: str | None,
    problem_id: str | None,
    page: int | None,
    page_size: int | None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    parameters: list[Any] = []
    if user_id is not None:
        conditions.append("user_id = ?")
        parameters.append(user_id)
    if problem_id is not None:
        conditions.append("problem_id = ?")
        parameters.append(problem_id)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    async with get_db_connection() as db:
        query = f"SELECT * FROM access_logs{where} ORDER BY id DESC"
        query_parameters = list(parameters)
        if page_size is not None:
            query += " LIMIT ? OFFSET ?"
            query_parameters.extend([page_size, ((page or 1) - 1) * page_size])
        cursor = await db.execute(query, query_parameters)
        rows = await cursor.fetchall()
    return [
        {
            **dict(row),
            "status": str(row["status"]),
        }
        for row in rows
    ]
