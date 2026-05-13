"""FastAPI application for app.glintstone.org (server-rendered pages)."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api_client import APIClient
from app.routes import admin, collections, debug, dictionary, home, tablets
from core.database import close_pool, init_pool
from core.version import release_tag, version_payload

BASE_DIR = Path(__file__).parent

APP_VERSION = release_tag()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    app.state.api = APIClient()
    yield
    app.state.api.close()
    close_pool()


app = FastAPI(title="Glintstone Web", docs_url=None, redoc_url=None, lifespan=lifespan)


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
app.include_router(tablets.router)
app.include_router(collections.router)
app.include_router(dictionary.router)
app.include_router(admin.router)
app.include_router(debug.router)
