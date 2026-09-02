from pydantic import BaseModel

from app.models.enums import JudgeResult


class ProcessRunResult(BaseModel):
    timed_out: bool = False
    memory_exceeded: bool = False
    exit_code: int | None = None
    time_used: float = 0.0
    memory_used: int = 0
    stdout: str = ""
    stderr: str = ""
    decode_error: bool = False
    compile_error: bool = False
    compile_info: str | None = None
    system_error: str | None = None


class JudgeCaseResult(BaseModel):
    id: int
    result: JudgeResult
    score: int
    time: float
    memory: int
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    compile_info: str | None = None


class JudgeResultData(BaseModel):
    result: JudgeResult
    score: int
    counts: int
    total_time: float
    cases: list[JudgeCaseResult]
    compile_info: str | None = None
    error_info: str | None = None
