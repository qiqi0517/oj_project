from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    msg: str = "success",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    content = {
        "code": status_code,
        "msg": msg,
        "data": data,
    }
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
    )
