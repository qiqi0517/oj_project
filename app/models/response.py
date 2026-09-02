from typing import Generic, TypeVar

from pydantic import BaseModel

ResponseData = TypeVar("ResponseData")


class ApiResponse(BaseModel, Generic[ResponseData]):
    code: int
    msg: str
    data: ResponseData | None = None
