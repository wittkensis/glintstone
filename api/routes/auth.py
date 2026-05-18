"""Auth routes — ORCID OAuth, magic-link email, sessions, API keys."""

import json
import subprocess
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.dependencies import require_user
from api.repositories.api_key_repo import ApiKeyRepository
from api.repositories.session_repo import SessionRepository
from api.repositories.user_repo import UserRepository
from api.services import auth_service, email_service
from core.config import get_settings
from core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Pydantic request/response models ─────────────────────────────────────────


class OrcidExchangeRequest(BaseModel):
    code: str
    redirect_uri: str


class MagicLinkRequest(BaseModel):
    email: str


class MagicLinkVerifyRequest(BaseModel):
    token: str


class GenerateApiKeyRequest(BaseModel):
    label: str
    tier: str = "free"


# ── ORCID OAuth ───────────────────────────────────────────────────────────────


@router.post("/orcid/exchange")
def orcid_exchange(body: OrcidExchangeRequest, request: Request, conn=Depends(get_db)):
    settings = get_settings()
    if not settings.orcid_client_id or not settings.orcid_client_secret:
        raise HTTPException(status_code=503, detail="ORCID not configured")

    # Exchange auth code for access token via curl (avoids macOS SSL issues).
    token_result = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            f"{settings.orcid_base_url}/oauth/token",
            "-H",
            "Accept: application/json",
            "-H",
            "Content-Type: application/x-www-form-urlencoded",
            "-d",
            (
                f"client_id={settings.orcid_client_id}"
                f"&client_secret={settings.orcid_client_secret}"
                f"&grant_type=authorization_code"
                f"&code={body.code}"
                f"&redirect_uri={body.redirect_uri}"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    try:
        token_data = json.loads(token_result.stdout)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="ORCID token exchange failed")

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="ORCID exchange rejected")

    # Fetch userinfo.
    info_result = subprocess.run(
        [
            "curl",
            "-s",
            f"{settings.orcid_base_url}/oauth/userinfo",
            "-H",
            f"Authorization: Bearer {access_token}",
            "-H",
            "Accept: application/json",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    try:
        info = json.loads(info_result.stdout)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="ORCID userinfo fetch failed")

    orcid_sub = info.get("sub")
    if not orcid_sub:
        raise HTTPException(status_code=502, detail="ORCID userinfo missing sub")

    email = info.get("email") or f"{orcid_sub}@orcid.invalid"
    display_name = info.get("name")

    user_repo = UserRepository(conn)
    user = user_repo.create_user(
        email=email, display_name=display_name, orcid_id=orcid_sub
    )
    user_repo.link_auth_method(user["id"], "orcid", orcid_sub)
    if info.get("email_verified"):
        user_repo.verify_email(user["id"])
    conn.commit()

    return _create_session_response(user, conn, request, settings)


# ── Magic link ────────────────────────────────────────────────────────────────


@router.post("/magic-link/request")
def magic_link_request(body: MagicLinkRequest, request: Request):
    settings = get_settings()
    token = auth_service.sign_magic_link(body.email, settings.session_secret_key)
    web_url = settings.web_url
    link = f"{web_url}/auth/verify?token={token}"
    try:
        email_service.send_magic_link(body.email, link, settings)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Email delivery failed: %s", exc)
        raise HTTPException(status_code=503, detail="Email service unavailable. Contact the administrator.")
    return {"status": "sent"}


@router.post("/magic-link/verify")
def magic_link_verify(
    body: MagicLinkVerifyRequest, request: Request, conn=Depends(get_db)
):
    settings = get_settings()
    from itsdangerous import BadSignature, SignatureExpired

    try:
        email = auth_service.verify_magic_link(body.token, settings.session_secret_key)
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Link has expired")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid link")

    user_repo = UserRepository(conn)
    user = user_repo.create_user(email=email)
    user_repo.link_auth_method(user["id"], "magic_link", email)
    user_repo.verify_email(user["id"])
    conn.commit()

    return _create_session_response(user, conn, request, settings)


# ── Session management ────────────────────────────────────────────────────────


@router.delete("/session", status_code=204)
def logout(request: Request, user: dict = Depends(require_user), conn=Depends(get_db)):
    session_id = getattr(request.state, "session_id", None)
    if session_id:
        SessionRepository(conn).revoke(session_id)
        conn.commit()


@router.get("/me")
def me(user: dict = Depends(require_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user.get("display_name"),
        "orcid_id": user.get("orcid_id"),
        "email_verified_at": user.get("email_verified_at"),
    }


# ── API keys ──────────────────────────────────────────────────────────────────


@router.post("/api-keys", status_code=201)
def create_api_key(
    body: GenerateApiKeyRequest,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    raw_key, key_hash = auth_service.generate_api_key()
    repo = ApiKeyRepository(conn)
    row = repo.create(user["id"], key_hash, body.label, body.tier)
    conn.commit()
    return {**row, "key": raw_key}


@router.get("/api-keys")
def list_api_keys(user: dict = Depends(require_user), conn=Depends(get_db)):
    return ApiKeyRepository(conn).list_for_user(user["id"])


@router.delete("/api-keys/{key_id}", status_code=204)
def revoke_api_key(
    key_id: str,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    revoked = ApiKeyRepository(conn).revoke(key_id, user["id"])
    conn.commit()
    if not revoked:
        raise HTTPException(status_code=404, detail="Key not found")


# ── Internal helper ───────────────────────────────────────────────────────────


def _create_session_response(user: dict, conn, request: Request, settings) -> dict:
    raw_token = auth_service.generate_session_token()
    token_hash = auth_service.hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.session_lifetime_days
    )
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    SessionRepository(conn).create_session(
        user_id=user["id"],
        token_hash=token_hash,
        expires_at=expires_at,
        ip=ip,
        user_agent=user_agent,
    )
    conn.commit()

    return {
        "token": raw_token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name"),
            "orcid_id": user.get("orcid_id"),
        },
    }
