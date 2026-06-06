"""FastAPI application for app.glintstone.org (server-rendered pages)."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.api_client import AuthRequiredError, GlintstoneAPI
from app.transports import HttpxTransport
from core.config import get_settings
from app.routes import (
    account,
    admin,
    auth,
    collections,
    compositions,
    debug,
    dictionary,
    home,
    scholars,
    search,
    tablets,
)
from core.database import close_pool, init_pool
from core.version import release_tag, version_payload

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent

APP_VERSION = release_tag()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    settings = get_settings()
    app.state.api = GlintstoneAPI(HttpxTransport(base_url=settings.api_url))
    yield
    app.state.api.close()
    close_pool()


_VALID_THEMES = {"default", "lapis-clay", "scholars-studio", "instrument-panel"}
_THEME_COOKIE = "glintstone_theme"


class ThemeMiddleware(BaseHTTPMiddleware):
    """Read the theme cookie and expose it as request.state.theme.

    Falls back to 'default' for unknown or missing values so templates
    always have a safe string to work with.
    """

    async def dispatch(self, request: Request, call_next):
        raw = request.cookies.get(_THEME_COOKIE, "default")
        request.state.theme = raw if raw in _VALID_THEMES else "default"
        return await call_next(request)


class AuthGateMiddleware(BaseHTTPMiddleware):
    """Redirect unauthenticated requests to /auth/login.

    Everything under /auth/, /static/, and the system probes are open.
    All other paths require the session_token cookie.
    """

    _OPEN_PREFIXES = ("/auth/", "/static/")
    _OPEN_EXACT = {"/healthz", "/version"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self._OPEN_EXACT or any(
            path.startswith(p) for p in self._OPEN_PREFIXES
        ):
            return await call_next(request)
        if not request.cookies.get("session_token"):
            return RedirectResponse("/auth/login", status_code=302)
        return await call_next(request)


app = FastAPI(title="Glintstone Web", docs_url=None, redoc_url=None, lifespan=lifespan)

app.add_middleware(ThemeMiddleware)
app.add_middleware(AuthGateMiddleware)


@app.exception_handler(AuthRequiredError)
async def auth_required_handler(request: Request, exc: AuthRequiredError):
    """Expired or invalid session cookie — clear it and send to login."""
    response = RedirectResponse("/auth/login", status_code=302)
    response.delete_cookie("session_token")
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request, "errors/404.html", {}, status_code=404
        )
    return templates.TemplateResponse(
        request,
        "errors/error.html",
        {"status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
    return templates.TemplateResponse(request, "errors/500.html", {}, status_code=500)


@app.middleware("http")
async def add_release_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Glintstone-Release"] = APP_VERSION
    return response


@app.get("/healthz", include_in_schema=False)
def healthz():
    """Lightweight liveness probe — process is up, no DB hit."""
    return JSONResponse({"status": "ok", "release": APP_VERSION})


@app.get("/version", include_in_schema=False)
def version():
    return JSONResponse(version_payload())


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["app_version"] = APP_VERSION
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(home.router)
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(tablets.router)
app.include_router(compositions.router)
app.include_router(collections.router)
app.include_router(dictionary.router)
app.include_router(scholars.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(debug.router)
