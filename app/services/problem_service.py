from collections.abc import Mapping
from typing import Any

import aiosqlite
from fastapi import status

from app.models.enums import UserRole
from app.models.problem import (
    ProblemCreate,
    ProblemListItem,
    StudentProblemDetail,
    TeacherProblemDetail,
    ProblemUpdate,
)
from app.repositories import problem_repository
from app.utils.exceptions import AppError
from app.utils.time import to_iso8601, utc_now


async def list_problems(
    page: int,
    page_size: int,
) -> dict[str, Any]:
    problem_rows = await problem_repository.list_problems(
        page=page,
        page_size=page_size,
    )
    total = await problem_repository.count_problems()
    items = [
        ProblemListItem.model_validate(row)
        for row in problem_rows
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_problem_detail(
    problem_id: str,
    current_user: Mapping[str, Any],
) -> StudentProblemDetail | TeacherProblemDetail:
    problem = await problem_repository.get_problem_by_id(problem_id)
    if problem is None:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "problem not found",
        )
    role = current_user["role"]
    if role == UserRole.STUDENT.value:
        return StudentProblemDetail.model_validate(problem)
    elif role in {
        UserRole.TEACHER.value,
        UserRole.ADMIN.value,
    }:
        return TeacherProblemDetail.model_validate(problem)
    else:
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "permission denied",
        )


async def create_problem(
    problem: ProblemCreate,
) -> TeacherProblemDetail:
    existing_problem = await problem_repository.get_problem_by_id(
        problem.id
    )
    if existing_problem is not None:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "problem already exists",
        )
    now = to_iso8601(utc_now())
    try:
        created_problem = await problem_repository.create_problem(
            problem=problem,
            created_at=now,
            updated_at=now,
        )
    except aiosqlite.IntegrityError as exc:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "problem already exists",
        ) from exc
    return TeacherProblemDetail.model_validate(created_problem)


async def update_problem(
    problem_id: str,
    problem_data: ProblemUpdate,
) -> TeacherProblemDetail:
    existing_problem = await problem_repository.get_problem_by_id(problem_id)
    if existing_problem is None:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "problem not found",
        )
    update_data = problem_data.model_dump(
        mode="json",
        exclude={
            "test_cases",
        },
    )
    updated_problem = await problem_repository.update_problem(
        problem_id=problem_id,
        problem_data=update_data,
        test_cases=problem_data.test_cases,
        updated_at=to_iso8601(utc_now()),
    )
    return TeacherProblemDetail.model_validate(updated_problem)


async def delete_problem(
    problem_id: str,
) -> None:
    existing_problem = await problem_repository.get_problem_by_id(problem_id)
    if existing_problem is None:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "problem not found",
        )
    deleted = await problem_repository.delete_problem(problem_id)
    if not deleted:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "problem not found",
        )