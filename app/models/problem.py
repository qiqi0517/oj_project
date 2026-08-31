from pydantic import BaseModel
from app.models.enums import Difficulty


class Sample(BaseModel):
    input: str
    output: str


class TestCase(BaseModel):
    case_id: str
    input: str
    output: str
    score: int
    is_hidden: bool


class ProblemBase(BaseModel):
    id: str
    title: str
    description: str
    input_description: str
    output_description: str
    samples: list[Sample]
    constraints: str
    time_limit: float
    memory_limit: int
    difficulty: Difficulty
    tags: list[str]


class ProblemCreate(ProblemBase):
    test_cases: list[TestCase]


class ProblemDetail(ProblemBase):
    test_cases: list[TestCase]


class ProblemListItem(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    tags: list[str]
    time_limit: float
    memory_limit: int
