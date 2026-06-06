"""Session helpers for the app tier.

The AuthGateMiddleware in app/main.py already blocks unauthenticated requests
at the cookie-presence level. This module adds:

  get_session_token() — extract the raw cookie value from a request
  get_current_user()  — fetch the current user from the API using the session
                        cookie; returns None if not logged in or session invalid

Routes that need the current user dict (e.g. account page, register check)
use get_current_user() as a FastAPI dependency rather than calling the API
directly.
"""

from typing import Optional

from fastapi import Request


def get_session_token(request: Request) -> Optional[str]:
    """Return the session_token cookie value, or None if absent."""
    return request.cookies.get("session_token")


async def get_current_user(request: Request) -> Optional[dict]:
    """Return the current user dict from the API session lookup.

    Calls GET /auth/me on the API tier (which validates the token against
    user_sessions). Returns None if the cookie is absent or the token is
    expired/invalid. Never raises — the caller decides what to do with None.
    """
    token = get_session_token(request)
    if not token:
        return None
    api = request.app.state.api
    # get_me() degrades gracefully and returns {} on any error (including 401)
    user = api.get_me(token=token)
    return user if user else None
