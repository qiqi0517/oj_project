from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import SESSION_SECRET, ensure_directories
from app.repositories.database import init_database
from app.services.user_service import ensure_initial_admin
from app.utils.exceptions import (
    AppError,
    app_error_handler,
    unexpected_error_handler,
)
from app.routers import (
    auth,
    backups,
    health,
    logs,
    problems,
    submissions,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    ensure_directories()
    await init_database()
    await ensure_initial_admin()
    yield


app = FastAPI(
    title="OJ System API",
    lifespan=lifespan,
)

app.add_exception_handler(
    AppError,
    app_error_handler,  # type: ignore
)

app.add_exception_handler(
    Exception,
    unexpected_error_handler,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(problems.router)
app.include_router(submissions.router)
app.include_router(logs.router)
app.include_router(backups.router)