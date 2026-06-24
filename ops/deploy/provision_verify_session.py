#!/usr/bin/env python3
"""Provision a stable, read-only verify session for post-deploy smoke checks (#280).

Why this exists
---------------
Post-deploy authed render checks (the deploy-verifier agent confirming that
logged-in pages render) used to MINT a short-lived ``user_sessions`` row and then
DELETE it on every verification run. It reversed cleanly, but every deploy still
wrote-then-deleted a row in the live production sessions table — noise in an
auth-critical table, and a small race/footgun if a run aborted mid-way.

This script provisions ONCE a dedicated verify-only user and a single long-lived
session row. After that, ``smoke-with-auth.sh`` reuses the same token on every
deploy — no per-run mint, no per-run delete. The verify user is identity-only
(it owns no annotations, makes no writes); the session it holds is used purely to
satisfy the auth middleware so authed pages render for the smoke check.

It is **idempotent**: re-running reuses the existing user and the existing
non-expired session rather than churning the table. It only inserts a new session
row when none is live, and it never deletes.

Security
--------
The raw token is printed exactly once (it is only stored hashed in the DB, same
as any real session — see auth_service.hash_token). Capture it into the
``GLINTSTONE_VERIFY_TOKEN`` deploy secret. Anyone holding it can view the same
pages a logged-in reader sees — nothing more (the user performs no writes). Rotate
by re-running with ``--rotate``.

Usage
-----
    # First-time provision (prints the token to store as a secret):
    python -m ops.deploy.provision_verify_session

    # Force a fresh token (revokes the old verify session, mints one new one):
    python -m ops.deploy.provision_verify_session --rotate

    # Custom lifetime (default 365 days):
    python -m ops.deploy.provision_verify_session --days 90

Run it on the VPS (or anywhere with DATABASE_URL pointing at prod), as the app
DB user — it needs only the DML already granted to ``glintstone`` on ``users`` and
``user_sessions``.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running as a plain script (python ops/deploy/provision_verify_session.py)
# as well as a module — mirror the path bootstrap used by scripts/.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api.services.auth_service import generate_session_token, hash_token  # noqa: E402
from core.database import close_pool, get_connection, init_pool  # noqa: E402

VERIFY_EMAIL = "verify@glintstone.org"
VERIFY_DISPLAY_NAME = "Deploy Verify (read-only)"


def _ensure_verify_user(conn) -> str:
    """Return the verify user's id, creating the row if absent. Idempotent."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, display_name, email_verified_at)
            VALUES (%(email)s, %(name)s, now())
            ON CONFLICT (email) DO UPDATE SET display_name = EXCLUDED.display_name
            RETURNING id
            """,
            {"email": VERIFY_EMAIL, "name": VERIFY_DISPLAY_NAME},
        )
        row = cur.fetchone()
        return str(row["id"])


def _existing_live_session(conn, user_id: str) -> bool:
    """True if the verify user already has a non-expired session row."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM user_sessions
            WHERE user_id = %(uid)s AND expires_at > now()
            LIMIT 1
            """,
            {"uid": user_id},
        )
        return cur.fetchone() is not None


def _revoke_verify_sessions(conn, user_id: str) -> int:
    """Delete all sessions for the verify user (used by --rotate). Returns count."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM user_sessions WHERE user_id = %(uid)s",
            {"uid": user_id},
        )
        return cur.rowcount


def _mint_verify_session(conn, user_id: str, days: int) -> str:
    """Insert a single long-lived session row, return the RAW token (printed once)."""
    raw = generate_session_token()
    token_hash = hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_sessions (user_id, token_hash, expires_at, user_agent)
            VALUES (%(uid)s, %(hash)s, %(exp)s, %(ua)s)
            """,
            {
                "uid": user_id,
                "hash": token_hash,
                "exp": expires_at,
                "ua": "glintstone-deploy-verify",
            },
        )
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Revoke existing verify sessions and mint a fresh token.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Session lifetime in days (default 365).",
    )
    args = parser.parse_args()

    init_pool(min_size=0, max_size=2, timeout=30.0)
    try:
        with get_connection() as conn:
            user_id = _ensure_verify_user(conn)

            if args.rotate:
                revoked = _revoke_verify_sessions(conn, user_id)
                raw = _mint_verify_session(conn, user_id, args.days)
                conn.commit()
                print(f"# Rotated verify session (revoked {revoked} old).")
                _print_token(raw, args.days)
                return 0

            if _existing_live_session(conn, user_id):
                conn.rollback()
                print(
                    "# A live verify session already exists — no new row minted.\n"
                    "# The previously-printed token is still valid. Use --rotate to\n"
                    "# replace it (e.g. if the secret was lost or leaked).",
                    file=sys.stderr,
                )
                return 0

            raw = _mint_verify_session(conn, user_id, args.days)
            conn.commit()
            print("# Provisioned a new verify session.")
            _print_token(raw, args.days)
            return 0
    finally:
        close_pool()


def _print_token(raw: str, days: int) -> None:
    print(
        f"# Store this as the GLINTSTONE_VERIFY_TOKEN deploy secret (valid {days} days):"
    )
    print(raw)


if __name__ == "__main__":
    raise SystemExit(main())
