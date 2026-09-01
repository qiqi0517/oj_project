from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models.language import LanguageCreate
from app.services import language_service
from app.utils.auth import get_current_user
from app.utils.response import success_response


router = APIRouter(
    prefix="/api/languages",
    tags=["languages"],
)


@router.post("/")
async def create_language(
    payload: LanguageCreate,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    language = await language_service.register_language(payload)
    return success_response(
        data={"name": language.name},
        msg="language registered",
    )


@router.get("/")
async def list_languages() -> JSONResponse:
    names = await language_service.get_language_names()
    return success_response(data={"name": names})
