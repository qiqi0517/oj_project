from pydantic import BaseModel, ConfigDict, Field, field_validator


class Sample(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input: str
    output: str


class TestCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input: str
    output: str


class ProblemBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str
    input_description: str
    output_description: str
    samples: list[Sample] = Field(min_length=1)
    constraints: str
    testcases: list[TestCase] = Field(min_length=1)
    hint: str = ""
    source: str = ""
    tags: list[str] = Field(default_factory=list)
    time_limit: float = Field(default=3.0, gt=0)
    memory_limit: int = Field(default=128, gt=0)
    author: str = ""
    difficulty: str = ""
    public_cases: bool = False

    @field_validator(
        "id",
        "title",
        "description",
        "input_description",
        "output_description",
        "constraints",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class ProblemCreate(ProblemBase):
    pass


class ProblemUpdate(ProblemBase):
    pass


class ProblemDetail(ProblemBase):
    pass


class ProblemListItem(BaseModel):
    id: str
    title: str


class LogVisibilityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    public_cases: bool = False


class ProblemIdResponse(BaseModel):
    id: str


class LogVisibilityResponse(BaseModel):
    problem_id: str
    public_cases: bool
