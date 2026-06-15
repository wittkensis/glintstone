"""Shared slowapi rate limiter for the agentic / Claude-backed routes.

Lives in its own module (not api/main.py) so route modules can import the
`limiter` instance and the keying function without a circular import back to
the application object.

Keying: prefer the authenticated user id (set by AuthMiddleware on
`request.state.user`); fall back to the remote IP for unauthenticated callers.
The AI routes are auth-gated (see issue #119), so in practice the user-id path
is what caps a given scholar; the IP fallback is a defence-in-depth backstop.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def user_or_ip_key(request: Request) -> str:
    """Rate-limit key: authenticated user id, else remote IP."""
    user = getattr(request.state, "user", None)
    if user and user.get("id") is not None:
        return f"user:{user['id']}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=user_or_ip_key)
