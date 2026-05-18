"""App auth routes — login page, ORCID callback, magic-link verify, logout."""

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from core.config import get_settings

router = APIRouter(prefix="/auth")


def _session_token(request: Request) -> str | None:
    return request.cookies.get("session_token")


def _set_session_cookie(response, token: str) -> None:
    settings = get_settings()
    is_prod = settings.app_env != "local"
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=is_prod,
        domain=".glintstone.org" if is_prod else None,
        max_age=60 * 60 * 24 * settings.session_lifetime_days,
    )


@router.get("/login")
def login_page(request: Request):
    token = _session_token(request)
    if token:
        # Verify the token is still valid before redirecting.
        try:
            request.app.state.api.get("/auth/me", token=token)
            return RedirectResponse("/account", status_code=302)
        except httpx.HTTPStatusError:
            pass

    settings = get_settings()
    params = urlencode(
        {
            "client_id": settings.orcid_client_id or "",
            "response_type": "code",
            "scope": "/authenticate",
            "redirect_uri": f"{settings.web_url}/auth/callback/orcid",
        }
    )
    orcid_url = f"{settings.orcid_base_url}/oauth/authorize?{params}"

    settings = get_settings()
    from app.main import templates

    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"orcid_url": orcid_url, "api_url": settings.api_url},
    )


@router.get("/callback/orcid")
def orcid_callback(request: Request, code: str = ""):
    if not code:
        return RedirectResponse("/auth/login?error=no_code", status_code=302)

    settings = get_settings()
    api = request.app.state.api
    try:
        data = api.post(
            "/auth/orcid/exchange",
            json={
                "code": code,
                "redirect_uri": f"{settings.web_url}/auth/callback/orcid",
            },
        )
    except httpx.HTTPStatusError:
        return RedirectResponse("/auth/login?error=orcid_failed", status_code=302)

    response = RedirectResponse("/account", status_code=302)
    _set_session_cookie(response, data["token"])
    return response


@router.get("/verify")
def magic_link_verify(request: Request, token: str = ""):
    if not token:
        return RedirectResponse("/auth/login?error=no_token", status_code=302)

    api = request.app.state.api
    try:
        data = api.post("/auth/magic-link/verify", json={"token": token})
    except httpx.HTTPStatusError:
        return RedirectResponse("/auth/login?error=invalid_link", status_code=302)

    response = RedirectResponse("/account", status_code=302)
    _set_session_cookie(response, data["token"])
    return response


@router.post("/logout")
def logout(request: Request):
    token = _session_token(request)
    if token:
        try:
            request.app.state.api.delete("/auth/session", token=token)
        except Exception:
            pass

    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("session_token")
    return response
