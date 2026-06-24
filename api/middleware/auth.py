"""Auth middleware — resolves bearer token or API key on every request.

Injects `request.state.user` (dict with user fields) or `None` for
unauthenticated requests. Routes that require auth use the `require_user`
dependency in `api/dependencies.py`.

Both auth paths reload the FULL users row by id (the API-key path always did;
the session path was hardened to match in #461) so that any new users column is
automatically present on `request.state.user` without editing a hand-listed
SELECT — the #450 class of bug, where avatar_url/role/theme silently dropped
from the session join until someone remembered to add them.
"""

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from api.repositories.api_key_repo import ApiKeyRepository
from api.repositories.session_repo import SessionRepository
from api.repositories.user_repo import UserRepository
from api.services.auth_service import hash_token
from core.database import DictConnection, get_connection


def _load_session_user(conn: DictConnection, token_hash: str) -> Optional[dict]:
    """Resolve a session token to the full users row, or None.

    Resolves the session → user_id (no user columns selected), touches the
    session's last-seen, then reloads the WHOLE users row via find_by_id so
    every present and future column is carried — mirroring the API-key path.
    Returns a dict with an injected ``session_id`` key, or None if the session
    is missing / expired / its user no longer exists.
    """
    session_repo = SessionRepository(conn)
    sess = session_repo.resolve_session(token_hash)
    if not sess:
        return None
    user = UserRepository(conn).find_by_id(sess["user_id"])
    if not user:
        return None
    session_repo.touch(sess["session_id"])
    user = dict(user)
    user["session_id"] = sess["session_id"]
    return user


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        request.state.session_id = None

        auth = request.headers.get("Authorization", "")

        if auth.startswith("glst_"):
            # API key path — entire header value is the raw key
            key_hash = hash_token(auth)
            try:
                with get_connection() as conn:
                    api_key_repo = ApiKeyRepository(conn)
                    key_row = api_key_repo.find_by_hash(key_hash)
                    if key_row:
                        api_key_repo.touch(key_row["id"])
                        user_repo = UserRepository(conn)
                        user = user_repo.find_by_id(key_row["user_id"])
                        if user:
                            user = dict(user)
                            user["auth_tier"] = key_row["tier"]
                            request.state.user = user
            except Exception:
                pass  # pool may not be up during health checks; leave user=None

        elif auth.startswith("Bearer "):
            raw = auth.removeprefix("Bearer ").strip()
            token_hash = hash_token(raw)
            try:
                with get_connection() as conn:
                    user = _load_session_user(conn, token_hash)
                    if user:
                        request.state.user = user
                        request.state.session_id = user["session_id"]
            except Exception:
                pass

        if request.state.user is None:
            # Fall back to session_token cookie (browser JS calls from the web app).
            cookie_token = request.cookies.get("session_token")
            if cookie_token:
                token_hash = hash_token(cookie_token)
                try:
                    with get_connection() as conn:
                        user = _load_session_user(conn, token_hash)
                        if user:
                            request.state.user = user
                            request.state.session_id = user["session_id"]
                except Exception:
                    pass

        return await call_next(request)
