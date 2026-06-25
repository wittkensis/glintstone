"""Auth routes — ORCID OAuth, magic-link email, sessions, API keys."""

import json
import subprocess
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
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


class SetPasswordRequest(BaseModel):
    password: str


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
        raise HTTPException(
            status_code=503,
            detail="Email service unavailable. Contact the administrator.",
        )
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
        "avatar_url": user.get("avatar_url"),
        "role": user.get("role", "standard"),
        "theme": user.get("theme", "default"),
    }


@router.post("/password")
def set_password(
    body: SetPasswordRequest,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    """Set or change the password for the currently logged-in user.

    Additive auth (issue #451): the user is already authenticated via their
    session (magic-link / ORCID / existing password). This stores a PBKDF2
    hash so they can ALSO sign in with email + password going forward. It does
    not touch magic-link or ORCID, which keep working exactly as before.
    """
    password = body.password.strip()
    if len(password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )
    password_hash = auth_service.hash_password(password)
    UserRepository(conn).set_password_hash(user["id"], password_hash)
    conn.commit()
    return {"status": "ok"}


@router.post("/avatar")
def upload_avatar(
    file: UploadFile,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    data = file.file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 5 MB)")

    from core.storage import get_storage

    ext = "jpg"
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()

    storage = get_storage()
    key = f"avatars/{user['id']}.{ext}"
    storage.put(key, data, content_type=file.content_type or "image/jpeg")
    avatar_url = storage.public_url(key)

    UserRepository(conn).update_avatar_url(user["id"], avatar_url)
    conn.commit()
    return {"avatar_url": avatar_url}


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


# ── Email + invite-code auth (PRD-014) ───────────────────────────────────────


class EmailLoginRequest(BaseModel):
    email: str
    password: str


class EmailRegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    affiliation: str = ""
    invite_code: str


@router.post("/email/login")
def email_login(body: EmailLoginRequest, request: Request, conn=Depends(get_db)):
    """Authenticate with email + password. Returns session token."""
    settings = get_settings()
    user = UserRepository(conn).find_by_email(body.email)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not auth_service.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _create_session_response(user, conn, request, settings)


@router.post("/email/register")
def email_register(body: EmailRegisterRequest, request: Request, conn=Depends(get_db)):
    """Register with invite code. Creates account and returns session token."""
    settings = get_settings()
    with conn.cursor() as cur:
        # Validate invite code
        cur.execute(
            "SELECT id FROM invite_codes WHERE code = %(code)s AND used_at IS NULL",
            {"code": body.invite_code},
        )
        invite = cur.fetchone()
        if not invite:
            raise HTTPException(
                status_code=400, detail="Invalid or already-used invite code"
            )

        # Check email uniqueness
        existing = UserRepository(conn).find_by_email(body.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create user
        password_hash = auth_service.hash_password(body.password)
        cur.execute(
            """
            INSERT INTO users (email, display_name, password_hash, invite_code_id)
            VALUES (%(email)s, %(name)s, %(password_hash)s, %(invite_code_id)s)
            RETURNING *
            """,
            {
                "email": body.email,
                "name": body.name,
                "password_hash": password_hash,
                "invite_code_id": invite["id"],
            },
        )
        user = cur.fetchone()

        # Mark invite used
        cur.execute(
            "UPDATE invite_codes SET used_by_email = %(email)s, used_at = NOW() WHERE id = %(id)s",
            {"email": body.email, "id": invite["id"]},
        )

    return _create_session_response(user, conn, request, settings)


# ── Scholar identity — claims (#17) ───────────────────────────────────────────


class ScholarClaimRequest(BaseModel):
    scholar_id: int
    claim_note: str | None = None


@router.get("/orcid-match")
def orcid_match(user: dict = Depends(require_user), conn=Depends(get_db)):
    """The auto-match probe the post-login prompt calls.

    Returns the UNCLAIMED scholar record whose ``orcid`` equals the logged-in
    user's ``orcid_id``, or ``null``. The join is ``users.orcid_id =
    scholars.orcid``; both columns are unique. Cheap; drives the "We found your
    record" banner. We exclude scholars that already carry an approved claim so
    the banner never offers a record the user can't actually take.
    """
    orcid = user.get("orcid_id")
    if not orcid:
        return {"match": None}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.name, s.institution,
                   (SELECT COUNT(*) FROM publication_authors pa
                     WHERE pa.scholar_id = s.id) AS publication_count
            FROM scholars s
            WHERE s.orcid = %s
              AND NOT EXISTS (
                  SELECT 1 FROM scholar_claims c
                  WHERE c.scholar_id = s.id AND c.status = 'approved'
              )
            LIMIT 1
            """,
            (orcid,),
        )
        row = cur.fetchone()
    return {"match": dict(row) if row else None}


@router.post("/scholar-claims", status_code=201)
def create_scholar_claim(
    body: ScholarClaimRequest,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    """File a claim on a scholar record.

    If the user's ``orcid_id`` matches ``scholars.orcid`` → the claim is created
    ``approved`` / ``orcid_match`` instantly (ORCID is a verified global identity;
    no admin step adds safety). Otherwise it is ``pending`` / ``manual_review``
    and goes to the admin queue. Rejects with 409 if the scholar already has an
    approved claim (one person per scholar) or if this user already has a pending
    claim on the same record.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT id, orcid FROM scholars WHERE id = %s", (body.scholar_id,))
        scholar = cur.fetchone()
        if not scholar:
            raise HTTPException(status_code=404, detail="Scholar not found")

        # Already claimed by someone (approved) → 409, offer the dispute path.
        cur.execute(
            "SELECT 1 FROM scholar_claims "
            "WHERE scholar_id = %s AND status = 'approved'",
            (body.scholar_id,),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=409, detail="This scholar record has already been claimed."
            )

        # This user already has a pending claim on this scholar → 409 (no spam).
        cur.execute(
            "SELECT 1 FROM scholar_claims "
            "WHERE scholar_id = %s AND user_id = %s AND status = 'pending'",
            (body.scholar_id, user["id"]),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=409,
                detail="You already have a pending claim on this record.",
            )

        # ORCID auto-match: the user authenticated against this ORCID at login.
        user_orcid = user.get("orcid_id")
        is_orcid_match = bool(
            user_orcid and scholar["orcid"] and scholar["orcid"] == user_orcid
        )
        if is_orcid_match:
            cur.execute(
                """
                INSERT INTO scholar_claims
                    (user_id, scholar_id, status, verification_method,
                     claim_note, verified_at)
                VALUES (%s, %s, 'approved', 'orcid_match', %s, now())
                RETURNING *
                """,
                (user["id"], body.scholar_id, body.claim_note),
            )
            claim = cur.fetchone()
            # Create the empty overlay shell so the bio editor is immediately
            # available. ON CONFLICT (not try/except) per the psycopg rollback trap.
            cur.execute(
                """
                INSERT INTO scholar_overrides (scholar_id, edited_by_user_id)
                VALUES (%s, %s)
                ON CONFLICT (scholar_id) DO NOTHING
                """,
                (body.scholar_id, user["id"]),
            )
        else:
            cur.execute(
                """
                INSERT INTO scholar_claims
                    (user_id, scholar_id, status, verification_method, claim_note)
                VALUES (%s, %s, 'pending', 'manual_review', %s)
                RETURNING *
                """,
                (user["id"], body.scholar_id, body.claim_note),
            )
            claim = cur.fetchone()
    conn.commit()
    return dict(claim)


@router.get("/scholar-claims/me")
def my_scholar_claims(user: dict = Depends(require_user), conn=Depends(get_db)):
    """The signed-in user's claims, newest first, with the scholar's name.

    Drives the /account "Scholar identity" status surface and the post-login
    prompt's dismissal logic.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.scholar_id, c.status, c.verification_method,
                   c.claim_note, c.claimed_at, c.verified_at, c.review_note,
                   s.name AS scholar_name, s.institution AS scholar_institution
            FROM scholar_claims c
            JOIN scholars s ON s.id = c.scholar_id
            WHERE c.user_id = %s
            ORDER BY c.claimed_at DESC
            """,
            (user["id"],),
        )
        rows = cur.fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/scholar-claims/{claim_id}/withdraw", status_code=204)
def withdraw_scholar_claim(
    claim_id: str, user: dict = Depends(require_user), conn=Depends(get_db)
):
    """Withdraw a pending claim. Sets status='rejected' with a withdrawn note
    rather than hard-deleting, keeping a clean audit row (spec open-question #1
    default). Only the owner can withdraw, and only while pending.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE scholar_claims
               SET status = 'rejected', review_note = 'Withdrawn by user'
             WHERE id = %s AND user_id = %s AND status = 'pending'
            """,
            (claim_id, user["id"]),
        )
        updated = cur.rowcount
    conn.commit()
    if not updated:
        raise HTTPException(status_code=404, detail="No pending claim to withdraw")


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
