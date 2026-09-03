import aiosqlite
from fastapi import status

from app.config import DEFAULT_MEMORY_LIMIT, DEFAULT_TIME_LIMIT
from app.judge.runner import PYTHON_RUN_COMMAND, validate_language_commands
from app.models.language import (
    LanguageCreate,
    LanguageCreateResponse,
    LanguageListResponse,
    LanguagePublic,
)
from app.repositories import language_repository
from app.utils.exceptions import AppError

DEFAULT_LANGUAGES = (
    LanguageCreate(
        name="python",
        file_ext=".py",
        run_cmd=PYTHON_RUN_COMMAND,
        time_limit=DEFAULT_TIME_LIMIT,
        memory_limit=DEFAULT_MEMORY_LIMIT,
    ),
    LanguageCreate(
        name="cpp",
        file_ext=".cpp",
        compile_cmd="g++ {src} -std=c++14 -o {exe}",
        run_cmd="{exe}",
        time_limit=DEFAULT_TIME_LIMIT,
        memory_limit=DEFAULT_MEMORY_LIMIT,
    ),
)


async def ensure_default_languages() -> None:
    for language in DEFAULT_LANGUAGES:
        await language_repository.ensure_language(language)


async def register_language(language: LanguageCreate) -> LanguageCreateResponse:
    try:
        validate_language_commands(language.compile_cmd, language.run_cmd)
    except ValueError as exc:
        raise AppError(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if await language_repository.get_language(language.name) is not None:
        raise AppError(status.HTTP_400_BAD_REQUEST, "language already exists")
    try:
        created = await language_repository.create_language(language)
    except aiosqlite.IntegrityError as exc:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "language already exists",
        ) from exc
    return LanguageCreateResponse.model_validate(created)


async def get_language(name: str) -> LanguagePublic:
    language = await language_repository.get_language(name)
    if language is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "language not found")
    return LanguagePublic.model_validate(language)


async def get_language_names() -> LanguageListResponse:
    languages = await language_repository.list_languages()
    return LanguageListResponse.model_validate(
        {"name": [language["name"] for language in languages]}
    )
