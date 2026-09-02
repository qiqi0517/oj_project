from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models.problem import (
    LogVisibilityResponse,
    LogVisibilityUpdate,
    ProblemCreate,
    ProblemDetail,
    ProblemIdResponse,
    ProblemListItem,
    ProblemUpdate,
)
from app.models.response import ApiResponse
from app.services import problem_service
from app.utils.auth import get_current_user, require_admin
from app.utils.response import success_response

router = APIRouter(
    prefix="/api/problems",
    tags=["problems"],
)


@router.get("/", response_model=ApiResponse[list[ProblemListItem]])
async def list_problems(
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    return success_response(data=await problem_service.list_problems())


@router.post("/", response_model=ApiResponse[ProblemIdResponse])
async def create_problem(
    payload: ProblemCreate,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    data = await problem_service.create_problem(payload)
    return success_response(
        data=data,
        msg="add success",
    )


@router.get("/{problem_id}", response_model=ApiResponse[ProblemDetail])
async def get_problem(
    problem_id: str,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    problem = await problem_service.get_problem_detail(problem_id)
    return success_response(data=problem)


@router.put("/{problem_id}", response_model=ApiResponse[ProblemIdResponse])
async def update_problem(
    problem_id: str,
    payload: ProblemUpdate,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    data = await problem_service.update_problem(problem_id, payload)
    return success_response(
        data=data,
        msg="update success",
    )


@router.delete("/{problem_id}", response_model=ApiResponse[ProblemIdResponse])
async def delete_problem(
    problem_id: str,
    _current_user: dict[str, Any] = Depends(require_admin),
) -> JSONResponse:
    data = await problem_service.delete_problem(problem_id)
    return success_response(
        data=data,
        msg="delete success",
    )


@router.put(
    "/{problem_id}/log_visibility",
    response_model=ApiResponse[LogVisibilityResponse],
)
async def update_log_visibility(
    problem_id: str,
    payload: LogVisibilityUpdate,
    _current_user: dict[str, Any] = Depends(require_admin),
) -> JSONResponse:
    data = await problem_service.set_log_visibility(
        problem_id,
        payload.public_cases,
    )
    return success_response(
        data=data,
        msg="log visibility updated",
    )
