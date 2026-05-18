"""FastAPI application for api.glintstone.org."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.database import init_pool, close_pool
from core.version import release_tag, version_payload
from api.middleware.auth import AuthMiddleware
from api.routes import (
    health,
    image,
    stats,
    artifacts,
    collections,
    composites,
    dictionary,
    scholars,
    search,
    agent,
    auth,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()


settings = get_settings()

app = FastAPI(
    title="Glintstone API",
    version=release_tag(),
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def add_release_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Glintstone-Release"] = release_tag()
    return response


@app.get("/version", tags=["meta"])
def version():
    """Release tag, environment, applied schema version, and process start time."""
    return version_payload()


app.add_middleware(AuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.web_url,
        f"http://localhost:{settings.web_port}",
        "https://app.glintstone.org",
        settings.www_url,
        f"http://localhost:{settings.www_port}",
        "https://glintstone.org",
        "https://www.glintstone.org",
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
app.include_router(scholars.router)
app.include_router(search.router)
app.include_router(agent.router)
app.include_router(agent.corrections_router)
app.include_router(auth.router)
app.include_router(users.router)
