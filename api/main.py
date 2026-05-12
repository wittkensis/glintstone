"""FastAPI application for api.glintstone.org."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.database import init_pool, close_pool
from api.routes import (
    health,
    image,
    stats,
    artifacts,
    collections,
    composites,
    dictionary,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()


settings = get_settings()

_version_file = Path(__file__).parent.parent / "version.txt"
_app_version = (
    _version_file.read_text().strip()
    if _version_file.exists()
    else os.getenv("APP_VERSION", "dev")
)

app = FastAPI(
    title="Glintstone API",
    version=_app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.web_url,
        f"http://localhost:{settings.web_port}",
        "https://app.glintstone.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(image.router)
app.include_router(stats.router)
app.include_router(artifacts.router)
app.include_router(collections.router)
app.include_router(composites.router)
app.include_router(dictionary.router)
