from pydantic import BaseModel, ConfigDict, Field, field_validator


class LanguageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=32)
    file_ext: str = Field(min_length=2, max_length=16)
    compile_cmd: str | None = None
    run_cmd: str = Field(min_length=1)
    time_limit: float | None = Field(default=None, gt=0)
    memory_limit: int | None = Field(default=None, gt=0)

    @field_validator("file_ext")
    @classmethod
    def validate_file_ext(cls, value: str) -> str:
        if not value.startswith("."):
            raise ValueError("file_ext must start with a dot")
        return value


class LanguagePublic(LanguageCreate):
    pass
