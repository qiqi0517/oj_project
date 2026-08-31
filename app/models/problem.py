from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import Difficulty


class Sample(BaseModel):
    input: str
    output: str


class TestCase(BaseModel):
    case_id: str
    input: str
    output: str
    score: int = Field(ge=0)
    is_hidden: bool


class ProblemContent(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str
    input_description: str
    output_description: str
    samples: list[Sample] = Field(min_length=1)
    constraints: str
    time_limit: float = Field(gt=0)
    memory_limit: int = Field(gt=0)
    difficulty: Difficulty
    tags: list[str]
    # validate that description, input_description, output_description is not blank
    @field_validator(
        "description",
        "input_description",
        "output_description",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class ProblemUpdate(ProblemContent):
    model_config = ConfigDict(extra="forbid")
    test_cases: list[TestCase] = Field(min_length=1)
    @model_validator(mode="after")
    def validate_problem_test_cases(self) -> Self:
        validate_test_cases(self.test_cases)
        return self


class ProblemBase(ProblemContent):
    id: str = Field(
        min_length=1,
        max_length=32,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class StudentProblemDetail(ProblemBase):
    pass


class ProblemWithTestCases(ProblemBase):
    test_cases: list[TestCase] = Field(min_length=1)
    @model_validator(mode="after")
    def validate_problem_test_cases(self) -> Self:
        validate_test_cases(self.test_cases)
        return self


class ProblemCreate(ProblemWithTestCases):
    pass


class TeacherProblemDetail(ProblemWithTestCases):
    pass


class ProblemListItem(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    tags: list[str]
    time_limit: float
    memory_limit: int


def validate_test_cases(test_cases: list[TestCase]) -> None:
    case_ids = [case.case_id for case in test_cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("test case ids must be unique")
    total_score = sum(case.score for case in test_cases)
    if total_score != 100:
        raise ValueError("test case scores must sum to 100")