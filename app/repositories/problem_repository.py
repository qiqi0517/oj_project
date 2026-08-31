import json
from collections.abc import Mapping
from typing import Any
import aiosqlite

from app.models.problem import ProblemCreate, TestCase
from app.repositories.database import get_db_connection


def _loads_json(value: str) -> Any:
    return json.loads(value)


def _dumps_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def _row_to_problem(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "input_description": row["input_description"],
        "output_description": row["output_description"],
        "samples": _loads_json(row["samples"]),
        "constraints": row["constraints"],
        "time_limit": row["time_limit"],
        "memory_limit": row["memory_limit"],
        "difficulty": row["difficulty"],
        "tags": _loads_json(row["tags"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _row_to_test_case(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "case_id": row["case_id"],
        "input": row["input_data"],
        "output": row["expected_output"],
        "score": row["score"],
        "is_hidden": bool(row["is_hidden"]),
    }


async def _insert_test_cases(
    db: aiosqlite.Connection,
    problem_id: str,
    test_cases: list[TestCase],
) -> None:
    for test_case in test_cases:
        await db.execute(
            """
            INSERT INTO test_cases (
                problem_id,
                case_id,
                input_data,
                expected_output,
                score,
                is_hidden
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                problem_id,
                test_case.case_id,
                test_case.input,
                test_case.output,
                test_case.score,
                int(test_case.is_hidden),
            ),
        )


async def list_problems(
    page: int,
    page_size: int,
) -> list[dict[str, Any]]:
    offset = (page - 1) * page_size
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT
                id,
                title,
                difficulty,
                tags,
                time_limit,
                memory_limit
            FROM problems
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        )
        rows = await cursor.fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "difficulty": row["difficulty"],
            "tags": _loads_json(row["tags"]),
            "time_limit": row["time_limit"],
            "memory_limit": row["memory_limit"],
        }
        for row in rows
    ]


async def count_problems() -> int:
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*) AS count
            FROM problems
            """
        )
        row = await cursor.fetchone()
    return row["count"]     # type: ignore


async def get_problem_by_id(
    problem_id: str,
) -> dict[str, Any] | None:
    async with get_db_connection() as db:
        # select problem
        cursor = await db.execute(
            """
            SELECT
                id,
                title,
                description,
                input_description,
                output_description,
                samples,
                constraints,
                time_limit,
                memory_limit,
                difficulty,
                tags,
                created_at,
                updated_at
            FROM problems
            WHERE id = ?
            """,
            (problem_id,),
        )
        problem_row = await cursor.fetchone()
        if problem_row is None:
            return None
        # select test_cases
        cursor = await db.execute(
            """
            SELECT
                case_id,
                input_data,
                expected_output,
                score,
                is_hidden
            FROM test_cases
            WHERE problem_id = ?
            ORDER BY case_id
            """,
            (problem_id,),
        )
        test_case_rows = await cursor.fetchall()
    problem = _row_to_problem(problem_row)
    problem["test_cases"] = [
        _row_to_test_case(row)
        for row in test_case_rows
    ]
    return problem


async def create_problem(
    problem: ProblemCreate,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN")
            await db.execute(
                """
                INSERT INTO problems (
                    id,
                    title,
                    description,
                    input_description,
                    output_description,
                    samples,
                    constraints,
                    time_limit,
                    memory_limit,
                    difficulty,
                    tags,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    problem.id,
                    problem.title,
                    problem.description,
                    problem.input_description,
                    problem.output_description,
                    _dumps_json([
                            sample.model_dump()
                            for sample in problem.samples
                    ]),
                    problem.constraints,
                    problem.time_limit,
                    problem.memory_limit,
                    problem.difficulty.value,
                    _dumps_json(problem.tags),
                    created_at,
                    updated_at,
                ),
            )
            await _insert_test_cases(
                db,
                problem.id,
                problem.test_cases,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    created_problem = await get_problem_by_id(problem.id)
    if created_problem is None:
        raise RuntimeError("failed to load created problem")
    else:
        return created_problem


async def update_problem(
    problem_id: str,
    problem_data: Mapping[str, Any],
    test_cases: list[TestCase],
    updated_at: str,
) -> dict[str, Any]:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN")
            await db.execute(
                """
                UPDATE problems
                SET
                    title = ?,
                    description = ?,
                    input_description = ?,
                    output_description = ?,
                    samples = ?,
                    constraints = ?,
                    time_limit = ?,
                    memory_limit = ?,
                    difficulty = ?,
                    tags = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    problem_data["title"],
                    problem_data["description"],
                    problem_data["input_description"],
                    problem_data["output_description"],
                    _dumps_json(problem_data["samples"]),
                    problem_data["constraints"],
                    problem_data["time_limit"],
                    problem_data["memory_limit"],
                    problem_data["difficulty"],
                    _dumps_json(problem_data["tags"]),
                    updated_at,
                    problem_id,
                ),
            )
            await db.execute(
                """
                DELETE FROM test_cases
                WHERE problem_id = ?
                """,
                (problem_id,),
            )
            await _insert_test_cases(
                db,
                problem_id,
                test_cases,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    updated_problem = await get_problem_by_id(problem_id)
    if updated_problem is None:
        raise RuntimeError("failed to load updated problem")
    return updated_problem


async def delete_problem(
    problem_id: str,
) -> bool:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN")
            await db.execute(
                """
                DELETE FROM test_cases
                WHERE problem_id = ?
                """,
                (problem_id,),
            )
            cursor = await db.execute(
                """
                DELETE FROM problems
                WHERE id = ?
                """,
                (problem_id,),
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    return cursor.rowcount > 0
