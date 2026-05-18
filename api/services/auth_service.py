"""Pure auth utilities — no DB, no I/O."""

import hashlib
import secrets

from itsdangerous import URLSafeTimedSerializer


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Return (raw_key, key_hash). Raw key is shown once; only hash is stored."""
    raw = "glst_" + secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def sign_magic_link(email: str, secret_key: str) -> str:
    s = URLSafeTimedSerializer(secret_key)
    return s.dumps(email, salt="magic-link")


def verify_magic_link(token: str, secret_key: str, max_age_seconds: int = 900) -> str:
    """Return the email embedded in the token, or raise SignatureExpired / BadSignature."""
    s = URLSafeTimedSerializer(secret_key)
    return s.loads(token, salt="magic-link", max_age=max_age_seconds)
