"""Auth middleware — resolves bearer token or API key on every request.

Injects `request.state.user` (dict with user fields) or `None` for
unauthenticated requests. Routes that require auth use the `require_user`
dependency in `api/dependencies.py`.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from api.repositories.api_key_repo import ApiKeyRepository
from api.repositories.session_repo import SessionRepository
from api.services.auth_service import hash_token
from core.database import get_connection


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
                    repo = ApiKeyRepository(conn)
                    key_row = repo.find_by_hash(key_hash)
                    if key_row:
                        repo.touch(key_row["id"])
                        from api.repositories.user_repo import UserRepository

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
                    repo = SessionRepository(conn)
                    row = repo.find_by_token_hash(token_hash)
                    if row:
                        repo.touch(row["session_id"])
                        request.state.user = dict(row)
                        request.state.session_id = row["session_id"]
            except Exception:
                pass

        if request.state.user is None:
            # Fall back to session_token cookie (browser JS calls from the web app).
            cookie_token = request.cookies.get("session_token")
            if cookie_token:
                token_hash = hash_token(cookie_token)
                try:
                    with get_connection() as conn:
                        repo = SessionRepository(conn)
                        row = repo.find_by_token_hash(token_hash)
                        if row:
                            repo.touch(row["session_id"])
                            request.state.user = dict(row)
                            request.state.session_id = row["session_id"]
                except Exception:
                    pass

        return await call_next(request)
