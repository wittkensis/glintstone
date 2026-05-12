"""FastAPI application for app.glintstone.org (server-rendered pages)."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api_client import APIClient
from app.routes import admin, collections, dictionary, home, tablets
from core.database import close_pool, init_pool

BASE_DIR = Path(__file__).parent

# Version written by deploy.sh into each release dir; falls back to env or "dev".
_version_file = BASE_DIR.parent / "version.txt"
APP_VERSION = (
    _version_file.read_text().strip()
    if _version_file.exists()
    else os.getenv("APP_VERSION", "dev")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    app.state.api = APIClient()
    yield
    app.state.api.close()
    close_pool()


app = FastAPI(title="Glintstone Web", docs_url=None, redoc_url=None, lifespan=lifespan)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["app_version"] = APP_VERSION
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(home.router)
app.include_router(tablets.router)
app.include_router(collections.router)
app.include_router(dictionary.router)
app.include_router(admin.router)
