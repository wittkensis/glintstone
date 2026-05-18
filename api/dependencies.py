"""Shared FastAPI dependencies."""

from fastapi import HTTPException, Request


def require_user(request: Request) -> dict:
    """Raise 401 if the request has no authenticated user."""
    if request.state.user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.state.user
