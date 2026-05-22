"""Account page — profile, API keys, bookmarks."""

import httpx
from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel

from core.config import get_settings

router = APIRouter()


# ── Proxy helpers ─────────────────────────────────────────────────────────────
# JS runs on app.glintstone.test; the API lives on api.glintstone.test.
# Because the session_token cookie is scoped to app.glintstone.test, the browser
# cannot send it to the API directly. These thin proxies stay same-origin with
# the browser and forward the token server-side as a Bearer header.


class _SavedItemBody(BaseModel):
    item_type: str
    item_id: str


@router.post("/_me/saved-items", status_code=201)
def save_item_proxy(body: _SavedItemBody, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    result = request.app.state.api.post(
        "/users/me/saved-items",
        json={"item_type": body.item_type, "item_id": body.item_id},
        token=token,
    )
    return JSONResponse(result, status_code=201)


@router.delete("/_me/saved-items/{item_id}", status_code=204)
def delete_item_proxy(item_id: str, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    request.app.state.api.delete(f"/users/me/saved-items/{item_id}", token=token)
    return Response(status_code=204)


@router.post("/_me/avatar")
def avatar_proxy(file: UploadFile, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    data = file.file.read()
    settings = get_settings()
    try:
        r = httpx.post(
            f"{settings.api_url}/auth/avatar",
            files={"file": (file.filename, data, file.content_type or "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
        if not r.is_success:
            return Response(status_code=r.status_code, content=r.text)
        return JSONResponse(r.json())
    except Exception:
        return Response(status_code=500)


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
