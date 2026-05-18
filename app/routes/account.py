"""Account page — profile, API keys, bookmarks."""

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

router = APIRouter()


@router.get("/_me")
def me_proxy(request: Request):
    """Thin proxy so base.html JS can fetch user identity without exposing API_URL."""
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=204)
    try:
        user = request.app.state.api.get("/auth/me", token=token)
        return JSONResponse(user)
    except Exception:
        return Response(status_code=204)


@router.get("/account")
def account(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse("/auth/login", status_code=302)

    api = request.app.state.api
    try:
        user = api.get("/auth/me", token=token)
    except httpx.HTTPStatusError:
        response = RedirectResponse("/auth/login", status_code=302)
        response.delete_cookie("session_token")
        return response

    api_keys = []
    bookmarks = []
    try:
        api_keys = api.get("/auth/api-keys", token=token)
        bookmarks = api.get(
            "/users/me/saved-items", params={"item_type": "artifact"}, token=token
        )
    except Exception:
        pass

    from core.config import get_settings

    settings = get_settings()
    from app.main import templates

    return templates.TemplateResponse(
        request,
        "account/index.html",
        {
            "user": user,
            "api_keys": api_keys,
            "bookmarks": bookmarks,
            "api_url": settings.api_url,
        },
    )
