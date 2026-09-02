from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import JudgeResult, SubmissionStatus


class SubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: str = Field(min_length=1)
    language: str = Field(min_length=1)
    code: str


class SubmissionCreateResponse(BaseModel):
    submission_id: str
    status: SubmissionStatus


class CompileInfo(BaseModel):
    result: str
    message: str


class RunInfo(BaseModel):
    result: str
    message: str


class SubmissionPublic(BaseModel):
    submission_id: str
    status: SubmissionStatus
    score: int | None = None
    counts: int | None = None
    compile_info: CompileInfo | None = None
    run_info: RunInfo | None = None
    error_info: str | None = None


class SubmissionListItem(BaseModel):
    submission_id: str
    status: SubmissionStatus
    score: int | None = None
    counts: int | None = None


class SubmissionListResponse(BaseModel):
    total: int
    submissions: list[SubmissionListItem]


class JudgeCaseDetailResponse(BaseModel):
    id: int
    result: JudgeResult
    time: float
    memory: int


class SubmissionLogResponse(BaseModel):
    details: list[JudgeCaseDetailResponse]
    score: int
    counts: int
