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


# ── Scholar identity proxies (#17) ────────────────────────────────────────────
# Same-origin proxies so claim/bio/admin JS can reach the API with the session
# cookie forwarded as a Bearer token (the cookie is scoped to the app host).


class _ClaimBody(BaseModel):
    scholar_id: int
    claim_note: str | None = None


@router.post("/_me/scholar-claims", status_code=201)
def claim_scholar_proxy(body: _ClaimBody, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    from app.api_client import AuthRequiredError

    try:
        result = request.app.state.api.post(
            "/auth/scholar-claims",
            json={"scholar_id": body.scholar_id, "claim_note": body.claim_note},
            token=token,
        )
    except AuthRequiredError:
        return Response(status_code=401)
    except httpx.HTTPStatusError as exc:
        detail = "Could not file the claim."
        try:
            detail = exc.response.json().get("detail", detail)
        except Exception:
            pass
        return JSONResponse({"detail": detail}, status_code=exc.response.status_code)
    return JSONResponse(result, status_code=201)


@router.post("/_me/scholar-claims/{claim_id}/withdraw", status_code=204)
def withdraw_claim_proxy(claim_id: str, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    try:
        request.app.state.api.post(
            f"/auth/scholar-claims/{claim_id}/withdraw", token=token
        )
    except httpx.HTTPStatusError as exc:
        return Response(status_code=exc.response.status_code)
    return Response(status_code=204)


class _BioBody(BaseModel):
    bio: str | None = None
    institution: str | None = None
    homepage_url: str | None = None
    expertise_periods: str | None = None
    expertise_languages: str | None = None


@router.put("/_me/scholars/{scholar_id}/bio")
def bio_proxy(scholar_id: int, body: _BioBody, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    from app.api_client import AuthRequiredError

    try:
        result = request.app.state.api.put(
            f"/scholars/{scholar_id}/bio",
            json=body.model_dump(),
            token=token,
        )
    except AuthRequiredError:
        return Response(status_code=401)
    except httpx.HTTPStatusError as exc:
        detail = "Could not save the profile."
        try:
            detail = exc.response.json().get("detail", detail)
        except Exception:
            pass
        return JSONResponse({"detail": detail}, status_code=exc.response.status_code)
    return JSONResponse(result)


class _VerifyBody(BaseModel):
    action: str
    review_note: str | None = None


@router.post("/_me/admin/scholar-claims/{claim_id}/verify")
def verify_claim_proxy(claim_id: str, body: _VerifyBody, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return Response(status_code=401)
    from app.api_client import AuthRequiredError

    try:
        result = request.app.state.api.post(
            f"/admin/scholar-claims/{claim_id}/verify",
            json={"action": body.action, "review_note": body.review_note},
            token=token,
        )
    except AuthRequiredError:
        return Response(status_code=401)
    except httpx.HTTPStatusError as exc:
        detail = "Could not record the decision."
        try:
            detail = exc.response.json().get("detail", detail)
        except Exception:
            pass
        return JSONResponse({"detail": detail}, status_code=exc.response.status_code)
    return JSONResponse(result)


@router.get("/_me/orcid-match")
def orcid_match_proxy(request: Request):
    """Drives the post-login claim prompt. Returns the matched unclaimed scholar
    (or {match:null}). Degrades to no-match on any error so a probe failure
    simply shows no banner (spec: degrade quietly)."""
    token = request.cookies.get("session_token")
    if not token:
        return JSONResponse({"match": None})
    return JSONResponse(request.app.state.api.get_orcid_match(token))


@router.get("/_me/scholar-claims")
def my_claims_proxy(request: Request):
    """The signed-in user's claims, for the post-login banner's manual-nudge
    branch (only nudge users who have no claim yet)."""
    token = request.cookies.get("session_token")
    if not token:
        return JSONResponse({"items": []})
    return JSONResponse({"items": request.app.state.api.get_my_scholar_claims(token)})


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

    # Scholar identity (#17): the user's claims drive the "Scholar identity"
    # account-section (no-claim CTA / pending / rejected / approved + bio editor).
    scholar_claims = api.get_my_scholar_claims(token)

    settings = get_settings()
    from app.main import templates

    return templates.TemplateResponse(
        request,
        "account/index.html",
        {
            "user": user,
            "api_keys": api_keys,
            "bookmarks": bookmarks,
            "scholar_claims": scholar_claims,
            "api_url": settings.api_url,
        },
    )
