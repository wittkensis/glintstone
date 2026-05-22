"""Shared FastAPI dependencies."""

from fastapi import HTTPException, Request


def require_user(request: Request) -> dict:
    """Raise 401 if the request has no authenticated user."""
    if request.state.user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.state.user


def require_admin(request: Request) -> dict:
    """Raise 403 if the authenticated user is not an admin."""
    user = require_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
