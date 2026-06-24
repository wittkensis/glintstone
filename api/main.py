"""FastAPI application for api.glintstone.org."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.auth import AuthMiddleware
from api.routes import (
    agent,
    artifacts,
    auth,
    collections,
    composites,
    dictionary,
    health,
    image,
    periods,
    proveniences,
    scholars,
    search,
    stats,
    users,
)
from core.config import get_settings
from core.database import close_pool, init_pool
from core.version import release_tag, version_payload

logger = logging.getLogger(__name__)


def _warm_query_cache() -> None:
    """Pre-warm the popular query-embed cache (#253) off the request path.

    Runs in a background thread from startup so a cold ~1.4-1.9s Voyage embed is
    paid once at boot instead of on the first user search after a deploy. Fully
    best-effort: a missing key or a Voyage hiccup just leaves the queries to
    embed lazily on first use, exactly as before — it must never delay startup or
    crash the process.
    """
    try:
        from api.services.agent_service import _get_voyage
        from core.agent.search_engine import warm_query_cache

        n = warm_query_cache(_get_voyage())
        logger.info("query-embed warm-cache: %d queries pinned", n)
    except Exception as exc:  # never let warming break startup
        logger.warning("query-embed warm-cache skipped: %r", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    # Warm the popular query-embed cache in a daemon thread so the first hero
    # search after a deploy isn't cold (#253). Backgrounded so it never delays
    # the server accepting connections or the /health smoke test.
    import threading

    threading.Thread(
        target=_warm_query_cache, name="warm-query-cache", daemon=True
    ).start()
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
async def timing_and_release(request: Request, call_next):
    t0 = time.monotonic()
    response = await call_next(request)
    duration_ms = int((time.monotonic() - t0) * 1000)
    response.headers["X-Glintstone-Release"] = release_tag()
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    logger.info(
        "api %s %s %d duration_ms=%d",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
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
app.include_router(periods.router)
app.include_router(proveniences.router)
app.include_router(scholars.router)
app.include_router(search.router)
app.include_router(agent.router)
app.include_router(agent.composites_agent_router)
app.include_router(agent.corrections_router)
app.include_router(auth.router)
app.include_router(users.router)
