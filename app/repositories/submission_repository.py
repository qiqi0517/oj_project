import json
from typing import Any

import aiosqlite

from app.models.judge import JudgeResultData
from app.models.problem import TestCase
from app.repositories.database import get_db_connection


def _row_to_submission(row: aiosqlite.Row) -> dict[str, Any]:
    compile_info = None
    if row["compile_info"]:
        try:
            compile_info = json.loads(row["compile_info"])
        except json.JSONDecodeError:
            compile_info = {
                "result": "error",
                "message": row["compile_info"],
            }
    return {
        "submission_id": row["id"],
        "user_id": row["user_id"],
        "problem_id": row["problem_id"],
        "language": row["language"],
        "code": row["source_code"],
        "status": row["status"],
        "result": row["result"],
        "score": row["score"],
        "counts": row["counts"],
        "total_time": row["total_time"],
        "compile_info": compile_info,
        "run_info": json.loads(row["run_info"]) if row["run_info"] else None,
        "error_info": row["error_info"],
        "created_at": row["created_at"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
    }


async def create_submission(
    *,
    submission_id: str,
    user_id: str,
    problem_id: str,
    language: str,
    code: str,
    created_at: str,
) -> None:
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO submissions (
                id, user_id, problem_id, language, source_code,
                status, score, counts, created_at
            )
            VALUES (?, ?, ?, ?, ?, 'pending', 0, 0, ?)
            """,
            (
                submission_id,
                user_id,
                problem_id,
                language,
                code,
                created_at,
            ),
        )
        await db.execute(
            "UPDATE users SET submit_count = submit_count + 1 WHERE id = ?",
            (user_id,),
        )
        await db.commit()


async def count_recent_submissions(user_id: str, cutoff: str) -> int:
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM submissions
            WHERE user_id = ? AND created_at >= ?
            """,
            (user_id, cutoff),
        )
        row = await cursor.fetchone()
    return int(row[0]) if row else 0


async def get_submission(submission_id: str) -> dict[str, Any] | None:
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM submissions WHERE id = ?",
            (submission_id,),
        )
        row = await cursor.fetchone()
    return _row_to_submission(row) if row else None


async def get_submission_log_context(
    submission_id: str,
) -> dict[str, Any] | None:
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT s.id, s.user_id, s.problem_id, s.score, s.counts,
                   p.public_cases
            FROM submissions AS s
            JOIN problems AS p ON p.id = s.problem_id
            WHERE s.id = ?
            """,
            (submission_id,),
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    return {
        "submission_id": row["id"],
        "user_id": row["user_id"],
        "problem_id": row["problem_id"],
        "score": row["score"],
        "counts": row["counts"],
        "public_cases": bool(row["public_cases"]),
    }


async def get_case_details(submission_id: str) -> list[dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT case_id, result, time_used, memory_used
            FROM judge_logs
            WHERE submission_id = ?
            ORDER BY id
            """,
            (submission_id,),
        )
        rows = await cursor.fetchall()
    return [
        {
            "id": int(row["case_id"]),
            "result": row["result"],
            "time": row["time_used"],
            "memory": row["memory_used"] or 0,
        }
        for row in rows
    ]


async def list_submissions(
    *,
    user_id: str | None,
    problem_id: str | None,
    submission_status: str | None,
    page: int | None,
    page_size: int | None,
) -> tuple[list[dict[str, Any]], int]:
    conditions: list[str] = []
    parameters: list[Any] = []
    if user_id is not None:
        conditions.append("user_id = ?")
        parameters.append(user_id)
    if problem_id is not None:
        conditions.append("problem_id = ?")
        parameters.append(problem_id)
    if submission_status is not None:
        conditions.append("status = ?")
        parameters.append(submission_status)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    async with get_db_connection() as db:
        cursor = await db.execute(
            f"SELECT COUNT(*) FROM submissions{where}",
            parameters,
        )
        total_row = await cursor.fetchone()
        query = f"SELECT * FROM submissions{where} ORDER BY created_at DESC, id"
        query_parameters = list(parameters)
        if page_size is not None:
            query += " LIMIT ? OFFSET ?"
            query_parameters.extend([page_size, ((page or 1) - 1) * page_size])
        cursor = await db.execute(query, query_parameters)
        rows = await cursor.fetchall()
    return [_row_to_submission(row) for row in rows], int(total_row[0])  # type: ignore


async def set_submission_pending(
    submission_id: str,
    started_at: str,
) -> bool:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN")
            cursor = await db.execute(
                """
                UPDATE submissions
                SET status = 'pending', score = 0, counts = 0,
                    total_time = NULL, compile_info = NULL, run_info = NULL,
                    error_info = NULL, started_at = ?, finished_at = NULL
                WHERE id = ? AND status IN ('success', 'error')
                """,
                (started_at, submission_id),
            )
            if cursor.rowcount > 0:
                await db.execute(
                    "DELETE FROM judge_logs WHERE submission_id = ?",
                    (submission_id,),
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    return cursor.rowcount > 0


async def save_judge_result(
    *,
    submission_id: str,
    user_id: str,
    problem_id: str,
    testcases: list[TestCase],
    result: JudgeResultData,
    has_compile_step: bool,
    submission_status: str,
    finished_at: str,
) -> None:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN")
            cursor = await db.execute(
                "SELECT result FROM submissions WHERE id = ?",
                (submission_id,),
            )
            previous_row = await cursor.fetchone()
            previous_result = previous_row[0] if previous_row else None
            cursor = await db.execute(
                """
                SELECT COUNT(*) FROM submissions
                WHERE user_id = ? AND problem_id = ? AND result = 'AC' AND id != ?
                """,
                (user_id, problem_id, submission_id),
            )
            other_accepted = int((await cursor.fetchone())[0])  # type: ignore

            await db.execute(
                """
                UPDATE submissions
                SET status = ?, result = ?, score = ?, counts = ?, total_time = ?,
                    compile_info = ?, run_info = ?, error_info = ?, finished_at = ?
                WHERE id = ?
                """,
                (
                    submission_status,
                    result.result.value,
                    result.score,
                    result.counts,
                    result.total_time,
                    (
                        json.dumps(
                            {
                                "result": (
                                    "error"
                                    if result.result.value == "CE"
                                    else "success"
                                ),
                                "message": result.compile_info or "",
                            }
                        )
                        if has_compile_step
                        else None
                    ),
                    json.dumps(
                        {
                            "result": "finished",
                            "message": f"{len(result.cases)} test cases finished",
                        }
                    ),
                    result.error_info or "",
                    finished_at,
                    submission_id,
                ),
            )
            await db.execute(
                "DELETE FROM judge_logs WHERE submission_id = ?",
                (submission_id,),
            )
            for case, testcase in zip(result.cases, testcases):
                await db.execute(
                    """
                    INSERT INTO judge_logs (
                        submission_id, case_id, result, score, time_used,
                        memory_used, exit_code, input_data, stdout, stderr,
                        expected_output, is_hidden, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """,
                    (
                        submission_id,
                        str(case.id),
                        case.result.value,
                        case.score,
                        case.time,
                        case.memory,
                        case.exit_code,
                        testcase.input,
                        case.stdout,
                        case.stderr,
                        testcase.output,
                        finished_at,
                    ),
                )

            is_accepted = result.result.value == "AC"
            was_accepted = previous_result == "AC"
            if is_accepted and not was_accepted and other_accepted == 0:
                await db.execute(
                    "UPDATE users SET resolve_count = resolve_count + 1 WHERE id = ?",
                    (user_id,),
                )
            elif was_accepted and not is_accepted and other_accepted == 0:
                await db.execute(
                    """
                    UPDATE users
                    SET resolve_count = MAX(resolve_count - 1, 0)
                    WHERE id = ?
                    """,
                    (user_id,),
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def mark_submission_error(
    submission_id: str,
    error_info: str,
    finished_at: str,
) -> None:
    async with get_db_connection() as db:
        try:
            await db.execute("BEGIN")
            cursor = await db.execute(
                """
                SELECT user_id, problem_id, result
                FROM submissions
                WHERE id = ?
                """,
                (submission_id,),
            )
            previous_row = await cursor.fetchone()
            if previous_row is None:
                await db.rollback()
                return

            await db.execute(
                """
                UPDATE submissions
                SET status = 'error', result = NULL, score = 0, counts = 0,
                    total_time = NULL, compile_info = NULL, run_info = NULL,
                    error_info = ?, finished_at = ?
                WHERE id = ?
                """,
                (error_info, finished_at, submission_id),
            )

            if previous_row["result"] == "AC":
                cursor = await db.execute(
                    """
                    SELECT COUNT(*) FROM submissions
                    WHERE user_id = ? AND problem_id = ?
                        AND result = 'AC' AND id != ?
                    """,
                    (
                        previous_row["user_id"],
                        previous_row["problem_id"],
                        submission_id,
                    ),
                )
                other_accepted = int((await cursor.fetchone())[0])  # type: ignore
                if other_accepted == 0:
                    await db.execute(
                        """
                        UPDATE users
                        SET resolve_count = MAX(resolve_count - 1, 0)
                        WHERE id = ?
                        """,
                        (previous_row["user_id"],),
                    )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
