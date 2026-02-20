"""Dictionary route — placeholder."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/dictionary")


@router.get("")
def dictionary_index(request: Request):
    from app.main import templates
    return templates.TemplateResponse(
        "dictionary/index.html",
        {"request": request},
    )
