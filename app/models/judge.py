from pydantic import BaseModel

from app.models.enums import JudgeResult


class ProcessRunResult(BaseModel):
    timed_out: bool = False
    exit_code: int | None = None
    time_used: float = 0.0
    stdout: str = ""
    stderr: str = ""
    decode_error: bool = False
    system_error: str | None = None

# for a single test_case
class JudgeCaseResult(BaseModel):
    case_id: str
    result: JudgeResult
    score: int
    time_used: float
    exit_code: int | None
    stdout: str
    stderr: str
    message: str = ""

# for whole problem
class JudgeResultData(BaseModel):
    result: JudgeResult
    score: int
    total_time: float
    cases: list[JudgeCaseResult]