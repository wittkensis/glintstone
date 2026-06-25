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


class _PasswordBody(BaseModel):
    password: str


@router.post("/_me/password", status_code=204)
def set_password_proxy(body: _PasswordBody, request: Request):
    """Same-origin proxy so account-page JS can set a password (issue #451).

    The session_token cookie is scoped to the app host, so the browser cannot
    call the API directly; this forwards it server-side as a Bearer header.
    """
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    from app.api_client import AuthRequiredError

    try:
        request.app.state.api.post(
            "/auth/password",
            json={"password": body.password},
            token=token,
        )
    except AuthRequiredError:
        return Response(status_code=401)
    except httpx.HTTPStatusError as exc:
        # Surface the API's validation message (e.g. "Password must be at
        # least 8 characters") to the browser.
        detail = "Could not set password."
        try:
            detail = exc.response.json().get("detail", detail)
        except Exception:
            pass
        return JSONResponse({"detail": detail}, status_code=exc.response.status_code)
    return Response(status_code=204)


_VALID_THEMES = {"default", "lapis-clay", "scholars-studio", "instrument-panel"}


class _PreferencesBody(BaseModel):
    theme: str


@router.patch("/_me/preferences", status_code=204)
def preferences_proxy(body: _PreferencesBody, request: Request, response: Response):
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    if body.theme not in _VALID_THEMES:
        return Response(status_code=422)
    # Cookie is the source of truth for the theme on every page load.
    # Set it before the API write so a failing backend never reverts the choice.
    response.set_cookie(
        "glintstone_theme",
        body.theme,
        max_age=365 * 24 * 3600,
        samesite="lax",
        httponly=False,
    )
    try:
        request.app.state.api.patch(
            "/users/me/preferences",
            json={"theme": body.theme},
            token=token,
        )
    except Exception:
        pass  # DB sync is best-effort; cookie already guarantees the theme persists


@router.get("/_me")
def me_proxy(request: Request):
    """Thin proxy so base.html JS can fetch user identity without exposing API_URL."""
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=204)
    # get_me() degrades to {} on any error — return 204 on empty so JS knows no user
    user = request.app.state.api.get_me(token)
    if not user:
        return Response(status_code=204)
    return JSONResponse(user)


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

    # api-keys uses passthrough — it's a list response without a Page wrapper
    api_keys = []
    try:
        api_keys = api.get("/auth/api-keys", token=token)
    except Exception:
        pass

    bookmarks = api.get_saved_items({"item_type": "artifact"}, token)

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
