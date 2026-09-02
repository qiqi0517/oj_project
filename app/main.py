from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import SESSION_SECRET, ensure_directories
from app.repositories.database import init_database
from app.services.user_service import ensure_initial_admin
from app.services.language_service import ensure_default_languages
from app.services.submission_service import wait_for_judge_tasks
from app.utils.exceptions import (
    AppError,
    app_error_handler,
    http_error_handler,
    validation_error_handler,
    unexpected_error_handler,
)
from app.routers import (
    auth,
    backups,
    health,
    logs,
    languages,
    problems,
    reset,
    submissions,
    users,
)

# lifespan
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    ensure_directories()
    await init_database()
    await ensure_initial_admin()
    await ensure_default_languages()
    try:
        yield
    finally:
        await wait_for_judge_tasks()

# app
app = FastAPI(
    title="OJ System API",
    lifespan=lifespan,
)

# exception handler
app.add_exception_handler(
    AppError,
    app_error_handler,  # type: ignore
)

app.add_exception_handler(
    RequestValidationError,
    validation_error_handler,   # type: ignore
)

app.add_exception_handler(
    HTTPException,
    http_error_handler,  # type: ignore
)

app.add_exception_handler(
    Exception,
    unexpected_error_handler,
)

# middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
)

# router
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(problems.router)
app.include_router(languages.router)
app.include_router(reset.router)
app.include_router(submissions.router)
app.include_router(logs.router)
app.include_router(backups.router)
