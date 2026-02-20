"""FastAPI application for app.glintstone.org (server-rendered pages)."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.config import get_settings
from app.api_client import APIClient
from app.routes import home, tablets, collections, dictionary

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.api = APIClient()
    yield
    app.state.api.close()


app = FastAPI(title="Glintstone Web", docs_url=None, redoc_url=None, lifespan=lifespan)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(home.router)
app.include_router(tablets.router)
app.include_router(collections.router)
app.include_router(dictionary.router)
