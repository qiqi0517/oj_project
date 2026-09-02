import asyncio
from datetime import timedelta
from typing import Any
from uuid import uuid4

from fastapi import status

from app.judge.evaluator import evaluate_language
from app.models.enums import JudgeResult, SubmissionStatus
from app.models.language import LanguagePublic
from app.models.problem import ProblemDetail
from app.models.submission import (
    JudgeCaseDetailResponse,
    SubmissionCreate,
    SubmissionCreateResponse,
    SubmissionListItem,
    SubmissionListResponse,
    SubmissionLogResponse,
    SubmissionPublic,
)
from app.repositories import (
    language_repository,
    log_repository,
    problem_repository,
    submission_repository,
)
from app.utils.exceptions import AppError
from app.utils.time import to_iso8601, utc_now

judge_tasks: set[asyncio.Task[None]] = set()


def start_judge_task(submission_id: str) -> None:
    task = asyncio.create_task(judge_submission(submission_id))
    judge_tasks.add(task)
    task.add_done_callback(judge_tasks.discard)


async def wait_for_judge_tasks() -> None:
    """Finish active judge jobs before the application event loop closes."""
    while judge_tasks:
        await asyncio.gather(*list(judge_tasks), return_exceptions=True)


async def create_submission(
    payload: SubmissionCreate,
    current_user: dict[str, Any],
) -> SubmissionCreateResponse:
    cutoff = to_iso8601(utc_now() - timedelta(minutes=1))
    recent = await submission_repository.count_recent_submissions(
        current_user["id"],
        cutoff,
    )
    if recent >= 3:
        raise AppError(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "submission rate limit exceeded",
        )
    if await problem_repository.get_problem_by_id(payload.problem_id) is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "problem not found")
    if await language_repository.get_language(payload.language) is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "language not found")

    submission_id = str(uuid4())
    await submission_repository.create_submission(
        submission_id=submission_id,
        user_id=current_user["id"],
        problem_id=payload.problem_id,
        language=payload.language,
        code=payload.code,
        created_at=to_iso8601(utc_now()),
    )
    start_judge_task(submission_id)
    return SubmissionCreateResponse.model_validate(
        {
            "submission_id": submission_id,
            "status": SubmissionStatus.PENDING,
        }
    )


async def judge_submission(submission_id: str) -> None:
    submission = await submission_repository.get_submission(submission_id)
    if submission is None:
        return
    try:
        problem_row = await problem_repository.get_problem_by_id(
            submission["problem_id"]
        )
        language_row = await language_repository.get_language(submission["language"])
        if problem_row is None or language_row is None:
            raise RuntimeError("judge configuration not found")
        problem = ProblemDetail.model_validate(problem_row)
        language = LanguagePublic.model_validate(language_row)
        time_limit = problem.time_limit or language.time_limit or 3.0
        memory_limit = problem.memory_limit or language.memory_limit or 128
        result = await evaluate_language(
            submission["code"],
            problem.testcases,
            time_limit,
            memory_limit,
            language,
        )
        submission_status = (
            SubmissionStatus.ERROR.value
            if result.result == JudgeResult.UNK
            else SubmissionStatus.SUCCESS.value
        )
        await submission_repository.save_judge_result(
            submission_id=submission_id,
            user_id=submission["user_id"],
            problem_id=submission["problem_id"],
            testcases=problem.testcases,
            result=result,
            has_compile_step=language.compile_cmd is not None,
            submission_status=submission_status,
            finished_at=to_iso8601(utc_now()),
        )
    except Exception:
        await submission_repository.mark_submission_error(
            submission_id,
            "judge internal error",
            to_iso8601(utc_now()),
        )


def to_submission_public(row: dict[str, Any]) -> SubmissionPublic:
    pending = row["status"] == SubmissionStatus.PENDING.value
    return SubmissionPublic.model_validate(
        {
            "submission_id": row["submission_id"],
            "status": row["status"],
            "score": None if pending else row["score"],
            "counts": None if pending else row["counts"],
            "compile_info": None if pending else row["compile_info"],
            "run_info": None if pending else row["run_info"],
            "error_info": None if pending else row["error_info"],
        }
    )


async def get_submission_public(
    submission_id: str,
    current_user: dict[str, Any],
) -> SubmissionPublic:
    row = await submission_repository.get_submission(submission_id)
    if row is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "submission not found")
    if current_user["role"] != "admin" and row["user_id"] != current_user["id"]:
        raise AppError(status.HTTP_403_FORBIDDEN, "permission denied")
    return to_submission_public(row)


async def get_submission_log(
    submission_id: str,
    current_user: dict[str, Any],
) -> SubmissionLogResponse:
    context = await submission_repository.get_submission_log_context(submission_id)
    if context is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "submission not found")

    allowed = (
        current_user["role"] == "admin"
        or context["user_id"] == current_user["id"]
        or context["public_cases"]
    )
    access_status = status.HTTP_200_OK if allowed else status.HTTP_403_FORBIDDEN
    await log_repository.create_access_log(
        user_id=current_user["id"],
        problem_id=context["problem_id"],
        action="view_logs",
        access_time=to_iso8601(utc_now()),
        access_status=access_status,
    )
    if not allowed:
        raise AppError(status.HTTP_403_FORBIDDEN, "permission denied")

    details = await submission_repository.get_case_details(submission_id)
    return SubmissionLogResponse.model_validate(
        {
            "details": [
                JudgeCaseDetailResponse.model_validate(detail) for detail in details
            ],
            "score": context["score"],
            "counts": context["counts"],
        }
    )


async def list_submission_publics(
    *,
    user_id: str | None,
    problem_id: str | None,
    submission_status: SubmissionStatus | None,
    page: int | None,
    page_size: int | None,
    current_user: dict[str, Any],
) -> SubmissionListResponse:
    if user_id is None and problem_id is None:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "user_id or problem_id is required",
        )
    if page is not None and page_size is None:
        raise AppError(status.HTTP_400_BAD_REQUEST, "page_size is required")
    if current_user["role"] != "admin":
        if user_id is not None and user_id != current_user["id"]:
            raise AppError(status.HTTP_403_FORBIDDEN, "permission denied")
        user_id = current_user["id"]

    rows, total = await submission_repository.list_submissions(
        user_id=user_id,
        problem_id=problem_id,
        submission_status=(
            submission_status.value if submission_status is not None else None
        ),
        page=page,
        page_size=page_size,
    )
    submissions: list[SubmissionListItem] = []
    for row in rows:
        success = row["status"] == SubmissionStatus.SUCCESS.value
        item = SubmissionListItem.model_validate(
            {
                "submission_id": row["submission_id"],
                "status": row["status"],
                "score": row["score"] if success else None,
                "counts": row["counts"] if success else None,
            }
        )
        submissions.append(item)
    return SubmissionListResponse.model_validate(
        {"total": total, "submissions": submissions}
    )


async def rejudge_submission(submission_id: str) -> SubmissionCreateResponse:
    if await submission_repository.get_submission(submission_id) is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "submission not found")
    await submission_repository.set_submission_pending(
        submission_id,
        to_iso8601(utc_now()),
    )
    start_judge_task(submission_id)
    return SubmissionCreateResponse.model_validate(
        {
            "submission_id": submission_id,
            "status": SubmissionStatus.PENDING,
        }
    )
