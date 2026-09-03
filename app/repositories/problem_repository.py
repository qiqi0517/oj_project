import json
from typing import Any

import aiosqlite

from app.models.problem import ProblemCreate, TestCase
from app.repositories.database import get_db_connection


def _loads_json(value: str) -> Any:
    return json.loads(value)


def _dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _row_to_problem(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "input_description": row["input_description"],
        "output_description": row["output_description"],
        "samples": _loads_json(row["samples"]),
        "constraints": row["constraints"],
        "testcases": [],
        "hint": row["hint"],
        "source": row["source"],
        "tags": _loads_json(row["tags"]),
        "time_limit": row["time_limit"],
        "memory_limit": row["memory_limit"],
        "author": row["author"],
        "difficulty": row["difficulty"],
    }


async def _insert_testcases(
    db: aiosqlite.Connection,
    problem_id: str,
    testcases: list[TestCase],
) -> None:
    for index, testcase in enumerate(testcases, start=1):
        await db.execute(
            """
            INSERT INTO test_cases (
                problem_id, case_id, input_data, expected_output
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                problem_id,
                f"case_{index}",
                testcase.input,
                testcase.output,
            ),
        )


async def list_problems() -> list[dict[str, str]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT id, title FROM problems ORDER BY id")
        rows = await cursor.fetchall()
    return [{"id": row["id"], "title": row["title"]} for row in rows]


async def get_problem_by_id(problem_id: str) -> dict[str, Any] | None:
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM problems WHERE id = ?",
            (problem_id,),
        )
        problem_row = await cursor.fetchone()
        if problem_row is None:
            return None
        cursor = await db.execute(
            """
            SELECT input_data, expected_output
            FROM test_cases
            WHERE problem_id = ?
            ORDER BY id
            """,
            (problem_id,),
        )
        testcase_rows = await cursor.fetchall()
    problem = _row_to_problem(problem_row)
    problem["testcases"] = [
        {"input": row["input_data"], "output": row["expected_output"]}
        for row in testcase_rows
    ]
    return problem


async def create_problem(
    problem: ProblemCreate,
) -> dict[str, Any]:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN")
            await db.execute(
                """
                INSERT INTO problems (
                    id, title, description, input_description, output_description,
                    constraints, hint, source, time_limit, memory_limit, author,
                    difficulty, public_cases, tags, samples
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    problem.id,
                    problem.title,
                    problem.description,
                    problem.input_description,
                    problem.output_description,
                    problem.constraints,
                    problem.hint,
                    problem.source,
                    problem.time_limit,
                    problem.memory_limit,
                    problem.author,
                    problem.difficulty,
                    0,
                    _dumps_json(problem.tags),
                    _dumps_json([sample.model_dump() for sample in problem.samples]),
                ),
            )
            await _insert_testcases(db, problem.id, problem.testcases)
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    created = await get_problem_by_id(problem.id)
    if created is None:
        raise RuntimeError("failed to load created problem")
    return created


async def update_problem(
    problem_id: str,
    problem: ProblemCreate,
) -> dict[str, Any]:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN")
            await db.execute(
                """
                UPDATE problems
                SET title = ?, description = ?, input_description = ?,
                    output_description = ?, constraints = ?, hint = ?, source = ?,
                    time_limit = ?, memory_limit = ?, author = ?, difficulty = ?,
                    tags = ?, samples = ?
                WHERE id = ?
                """,
                (
                    problem.title,
                    problem.description,
                    problem.input_description,
                    problem.output_description,
                    problem.constraints,
                    problem.hint,
                    problem.source,
                    problem.time_limit,
                    problem.memory_limit,
                    problem.author,
                    problem.difficulty,
                    _dumps_json(problem.tags),
                    _dumps_json([sample.model_dump() for sample in problem.samples]),
                    problem_id,
                ),
            )
            await db.execute(
                "DELETE FROM test_cases WHERE problem_id = ?",
                (problem_id,),
            )
            await _insert_testcases(db, problem_id, problem.testcases)
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    updated = await get_problem_by_id(problem_id)
    if updated is None:
        raise RuntimeError("failed to load updated problem")
    return updated


async def update_log_visibility(
    problem_id: str,
    public_cases: bool,
) -> bool:
    async with get_db_connection() as db:
        cursor = await db.execute(
            "UPDATE problems SET public_cases = ? WHERE id = ?",
            (int(public_cases), problem_id),
        )
        await db.commit()
    return cursor.rowcount > 0


async def delete_problem(problem_id: str) -> bool:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute(
                "SELECT 1 FROM problems WHERE id = ?",
                (problem_id,),
            )
            if await cursor.fetchone() is None:
                await db.rollback()
                return False

            cursor = await db.execute(
                "SELECT DISTINCT user_id FROM submissions WHERE problem_id = ?",
                (problem_id,),
            )
            affected_user_ids = [
                row["user_id"] for row in await cursor.fetchall()
            ]

            await db.execute(
                """
                DELETE FROM judge_logs
                WHERE submission_id IN (
                    SELECT id FROM submissions WHERE problem_id = ?
                )
                """,
                (problem_id,),
            )
            await db.execute(
                "DELETE FROM submissions WHERE problem_id = ?",
                (problem_id,),
            )
            await db.execute(
                "DELETE FROM access_logs WHERE problem_id = ?",
                (problem_id,),
            )
            await db.execute(
                "DELETE FROM test_cases WHERE problem_id = ?",
                (problem_id,),
            )
            cursor = await db.execute(
                "DELETE FROM problems WHERE id = ?",
                (problem_id,),
            )

            for user_id in affected_user_ids:
                await db.execute(
                    """
                    UPDATE users
                    SET submit_count = (
                            SELECT COUNT(*) FROM submissions
                            WHERE user_id = ?
                        ),
                        resolve_count = (
                            SELECT COUNT(DISTINCT problem_id) FROM submissions
                            WHERE user_id = ? AND result = 'AC'
                        )
                    WHERE id = ?
                    """,
                    (user_id, user_id, user_id),
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    return cursor.rowcount > 0
