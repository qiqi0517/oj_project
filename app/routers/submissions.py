from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.models.enums import SubmissionStatus
from app.models.response import ApiResponse
from app.models.submission import (
    SubmissionCreate,
    SubmissionCreateResponse,
    SubmissionListResponse,
    SubmissionLogResponse,
    SubmissionPublic,
)
from app.services import submission_service
from app.utils.auth import get_current_user, require_admin
from app.utils.response import success_response


router = APIRouter(
    prefix="/api/submissions",
    tags=["submissions"],
)


@router.post("/", response_model=ApiResponse[SubmissionCreateResponse])
async def create_submission(
    payload: SubmissionCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    data = await submission_service.create_submission(payload, current_user)
    return success_response(data=data)


@router.get("/", response_model=ApiResponse[SubmissionListResponse])
async def list_submissions(
    user_id: str | None = None,
    problem_id: str | None = None,
    submission_status: SubmissionStatus | None = Query(
        default=None,
        alias="status",
    ),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    data = await submission_service.list_submission_publics(
        user_id=user_id,
        problem_id=problem_id,
        submission_status=submission_status,
        page=page,
        page_size=page_size,
        current_user=current_user,
    )
    return success_response(data=data)


@router.get("/{submission_id}", response_model=ApiResponse[SubmissionPublic])
async def get_submission(
    submission_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    data = await submission_service.get_submission_public(
        submission_id,
        current_user,
    )
    return success_response(data=data)


@router.get(
    "/{submission_id}/log",
    response_model=ApiResponse[SubmissionLogResponse],
)
async def get_submission_log(
    submission_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    data = await submission_service.get_submission_log(
        submission_id,
        current_user,
    )
    return success_response(data=data)


@router.put(
    "/{submission_id}/rejudge",
    response_model=ApiResponse[SubmissionCreateResponse],
)
async def rejudge_submission(
    submission_id: str,
    _current_user: dict[str, Any] = Depends(require_admin),
) -> JSONResponse:
    data = await submission_service.rejudge_submission(submission_id)
    return success_response(data=data, msg="rejudge started")
