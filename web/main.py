"""FastAPI application for app.glintstone.org (server-rendered pages)."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from glintstone.config import get_settings

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Glintstone Web", docs_url=None, redoc_url=None)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/")
def homepage(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "api_url": settings.api_url},
    )
