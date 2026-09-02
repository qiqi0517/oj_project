import aiosqlite
from fastapi import status

from app.models.problem import (
    LogVisibilityResponse,
    ProblemCreate,
    ProblemDetail,
    ProblemIdResponse,
    ProblemListItem,
    ProblemUpdate,
)
from app.repositories import problem_repository
from app.utils.exceptions import AppError


async def list_problems() -> list[ProblemListItem]:
    rows = await problem_repository.list_problems()
    return [ProblemListItem.model_validate(row) for row in rows]


async def get_problem_detail(problem_id: str) -> ProblemDetail:
    problem = await problem_repository.get_problem_by_id(problem_id)
    if problem is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "problem not found")
    return ProblemDetail.model_validate(problem)


async def create_problem(problem: ProblemCreate) -> ProblemIdResponse:
    if await problem_repository.get_problem_by_id(problem.id) is not None:
        raise AppError(status.HTTP_409_CONFLICT, "problem already exists")
    try:
        await problem_repository.create_problem(problem)
    except aiosqlite.IntegrityError as exc:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "problem already exists",
        ) from exc
    return ProblemIdResponse.model_validate({"id": problem.id})


async def update_problem(
    problem_id: str,
    problem: ProblemUpdate,
) -> ProblemIdResponse:
    if problem.id != problem_id:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "problem id does not match path",
        )
    if await problem_repository.get_problem_by_id(problem_id) is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "problem not found")
    await problem_repository.update_problem(
        problem_id,
        ProblemCreate.model_validate(problem.model_dump()),
    )
    return ProblemIdResponse.model_validate({"id": problem_id})


async def set_log_visibility(
    problem_id: str,
    public_cases: bool,
) -> LogVisibilityResponse:
    if not await problem_repository.update_log_visibility(
        problem_id,
        public_cases,
    ):
        raise AppError(status.HTTP_404_NOT_FOUND, "problem not found")
    return LogVisibilityResponse.model_validate(
        {"problem_id": problem_id, "public_cases": public_cases}
    )


async def delete_problem(problem_id: str) -> ProblemIdResponse:
    if not await problem_repository.delete_problem(problem_id):
        raise AppError(status.HTTP_404_NOT_FOUND, "problem not found")
    return ProblemIdResponse.model_validate({"id": problem_id})
