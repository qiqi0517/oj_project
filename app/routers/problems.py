from typing import Any

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.models.problem import ProblemCreate, ProblemUpdate
from app.services import problem_service
from app.utils.auth import (
    get_current_user,
    require_teacher_or_admin,
)
from app.utils.response import success_response


router = APIRouter(
    prefix="/api/problems",
    tags=["problems"],
)


@router.get("")
async def list_problems(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    data = await problem_service.list_problems(
        page=page,
        page_size=page_size,
    )
    return success_response(
        data=data,
        status_code=status.HTTP_200_OK,
    )


@router.get("/{problem_id}")
async def get_problem(
    problem_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    problem = await problem_service.get_problem_detail(
        problem_id=problem_id,
        current_user=current_user,
    )
    return success_response(
        data=problem,
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_problem(
    payload: ProblemCreate,
    current_user: dict[str, Any] = Depends(require_teacher_or_admin),
) -> JSONResponse:
    problem = await problem_service.create_problem(payload)
    return success_response(
        data=problem,
        message="problem created",
        status_code=status.HTTP_201_CREATED,
    )


@router.put("/{problem_id}")
async def update_problem(
    problem_id: str,
    payload: ProblemUpdate,
    current_user: dict[str, Any] = Depends(require_teacher_or_admin),
) -> JSONResponse:
    problem = await problem_service.update_problem(
        problem_id=problem_id,
        problem_data=payload,
    )
    return success_response(
        data=problem,
        message="problem updated",
        status_code=status.HTTP_200_OK,
    )


@router.delete("/{problem_id}")
async def delete_problem(
    problem_id: str,
    current_user: dict[str, Any] = Depends(require_teacher_or_admin),
) -> JSONResponse:
    await problem_service.delete_problem(problem_id)
    return success_response(
        data=None,
        message="problem deleted",
        status_code=status.HTTP_200_OK,
    )