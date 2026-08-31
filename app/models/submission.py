from datetime import datetime
from pydantic import BaseModel
from app.models.enums import (JudgeResult, Language, SubmissionStatus)


class SubmissionCreate(BaseModel):
    problem_id: str
    language: Language
    source_code: str


class SubmissionPublic(BaseModel):
    id: str
    user_id: str
    problem_id: str
    language: Language
    source_code: str
    status: SubmissionStatus
    result: JudgeResult | None
    score: int
    total_time: float | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None