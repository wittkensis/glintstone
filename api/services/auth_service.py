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


_PBKDF2_ALGO = "sha256"
_PBKDF2_ITERATIONS = 260_000


def hash_password(plain: str) -> str:
    """Hash a plain-text password with PBKDF2-SHA256 + random salt (stdlib only)."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGO, plain.encode(), salt.encode(), _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_{_PBKDF2_ALGO}${salt}${key.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time verification against a hash produced by hash_password."""
    try:
        algo_tag, salt, key_hex = hashed.split("$")
        if algo_tag != f"pbkdf2_{_PBKDF2_ALGO}":
            return False
        derived = hashlib.pbkdf2_hmac(
            _PBKDF2_ALGO, plain.encode(), salt.encode(), _PBKDF2_ITERATIONS
        )
        return secrets.compare_digest(derived.hex(), key_hex)
    except Exception:
        return False


def sign_magic_link(email: str, secret_key: str) -> str:
    s = URLSafeTimedSerializer(secret_key)
    return s.dumps(email, salt="magic-link")


def verify_magic_link(token: str, secret_key: str, max_age_seconds: int = 900) -> str:
    """Return the email embedded in the token, or raise SignatureExpired / BadSignature."""
    s = URLSafeTimedSerializer(secret_key)
    return s.loads(token, salt="magic-link", max_age=max_age_seconds)
