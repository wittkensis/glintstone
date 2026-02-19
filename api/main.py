"""FastAPI application for api.glintstone.org."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from glintstone.config import get_settings
from glintstone.database import init_pool, close_pool
from api.routes import health, image


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()


settings = get_settings()

app = FastAPI(
    title="Glintstone API",
    version="2.0.0-dev",
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
