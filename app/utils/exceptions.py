import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, status_code: int, msg: str):
        self.status_code = status_code
        self.msg = msg

        super().__init__(msg)


async def app_error_handler(
    _request: Request,
    exc: AppError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": exc.msg,
            "data": None,
        },
    )


async def validation_error_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": status.HTTP_400_BAD_REQUEST,
            "msg": "validation error",
            "data": None,
        },
    )


async def http_error_handler(
    _request: Request,
    exc: HTTPException,
) -> JSONResponse:
    msg = exc.detail if isinstance(exc.detail, str) else "request error"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": msg,
            "data": None,
        },
        headers=exc.headers,
    )


async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled exception for %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "msg": "internal server error",
            "data": None,
        },
    )
