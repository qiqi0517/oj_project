import aiosqlite
from fastapi import status

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
        run_cmd="python3 {src}",
        time_limit=3.0,
        memory_limit=128,
    ),
    LanguageCreate(
        name="cpp",
        file_ext=".cpp",
        compile_cmd="g++ {src} -std=c++14 -o {exe}",
        run_cmd="{exe}",
        time_limit=3.0,
        memory_limit=128,
    ),
)


async def ensure_default_languages() -> None:
    for language in DEFAULT_LANGUAGES:
        await language_repository.ensure_language(language)


async def register_language(language: LanguageCreate) -> LanguageCreateResponse:
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
