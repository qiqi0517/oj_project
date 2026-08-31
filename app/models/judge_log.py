from datetime import datetime
from pydantic import BaseModel
from app.models.enums import JudgeResult


class JudgeLog(BaseModel):
    id: int | None = None
    submission_id: str
    case_id: str
    result: JudgeResult
    score: int
    time_used: float
    memory_used: int | None
    exit_code: int | None
    input_data: str
    stdout: str
    stderr: str
    expected_output: str
    message: str | None
    is_hidden: bool
    created_at: datetime