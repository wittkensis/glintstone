"""App auth routes — login, registration, ORCID callback, magic-link verify, logout.

PRD-014 adds:
  GET  /auth/register   — registration form (invite code pre-filled from query param)
  POST /auth/register   — validate invite + create user via API → set session cookie
  POST /auth/login      — email + password login via API → set session cookie

All data operations go through the API tier (two-tier rule: app/ never touches DB).
The new email/password endpoints delegate to:
  POST /auth/email/login    — in api/routes/auth.py (needs to be added there)
  POST /auth/email/register — in api/routes/auth.py (needs to be added there)
"""

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from core.config import get_settings

router = APIRouter(prefix="/auth")


# ── Cookie helpers ─────────────────────────────────────────────────────────────


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


# ── Login ─────────────────────────────────────────────────────────────────────


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
        {
            "orcid_url": orcid_url,
            "api_url": settings.api_url,
            "error": request.query_params.get("error"),
        },
    )


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """Email + password login.

    Calls POST /auth/email/login on the API tier. The API validates the
    password hash and creates a session, returning {"token": "..."}.
    """
    api = request.app.state.api
    try:
        data = api.post(
            "/auth/email/login", json={"email": email, "password": password}
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return RedirectResponse(
                "/auth/login?error=invalid_credentials", status_code=302
            )
        return RedirectResponse("/auth/login?error=login_failed", status_code=302)
    except Exception:
        return RedirectResponse("/auth/login?error=login_failed", status_code=302)

    response = RedirectResponse("/", status_code=302)
    _set_session_cookie(response, data["token"])
    return response


# ── Registration ──────────────────────────────────────────────────────────────


@router.get("/register")
def register_page(request: Request, code: str = ""):
    """Registration form — invite code pre-filled from query param.

    Share the full URL with scholars: /auth/register?code=XXXX-XXXX-XXXX
    """
    token = _session_token(request)
    if token:
        try:
            request.app.state.api.get("/auth/me", token=token)
            return RedirectResponse("/", status_code=302)
        except Exception:
            pass

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {
            "invite_code": code,
            "error": request.query_params.get("error"),
        },
    )


@router.post("/register")
def register_submit(
    request: Request,
    name: str = Form(...),
    affiliation: str = Form(""),
    email: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(...),
):
    """Process registration.

    Calls POST /auth/email/register on the API tier, which:
      - validates the invite code (exists and unused)
      - hashes the password with PBKDF2-SHA256
      - creates the user row (name, affiliation, email, password_hash, invite_code_id)
      - marks the invite code used (used_by_email, used_at)
      - creates a session in user_sessions
      - returns {"token": "..."}
    """
    api = request.app.state.api
    try:
        data = api.post(
            "/auth/email/register",
            json={
                "name": name,
                "affiliation": affiliation,
                "email": email,
                "password": password,
                "invite_code": invite_code,
            },
        )
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 409:
            # Email already registered
            return RedirectResponse(
                f"/auth/register?code={invite_code}&error=email_taken", status_code=302
            )
        if status == 400:
            # Invite code problem — API embeds reason in detail
            try:
                detail = exc.response.json().get("detail", "").lower()
            except Exception:
                detail = ""
            if "already used" in detail or "code_used" in detail:
                reason = "code_used"
            elif "invite" in detail:
                reason = "invalid_code"
            else:
                reason = "invalid_request"
            return RedirectResponse(
                f"/auth/register?code={invite_code}&error={reason}", status_code=302
            )
        return RedirectResponse("/auth/register?error=register_failed", status_code=302)
    except Exception:
        return RedirectResponse("/auth/register?error=register_failed", status_code=302)

    response = RedirectResponse("/", status_code=302)
    _set_session_cookie(response, data["token"])
    return response


# ── ORCID callback ────────────────────────────────────────────────────────────


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


# ── Magic-link verify ─────────────────────────────────────────────────────────


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


# ── Logout ────────────────────────────────────────────────────────────────────


@router.post("/logout")
def logout(request: Request):
    token = _session_token(request)
    if token:
        try:
            request.app.state.api.delete("/auth/session", token=token)
        except Exception:
            pass

    response = RedirectResponse("/auth/login", status_code=302)
    response.delete_cookie("session_token")
    return response
