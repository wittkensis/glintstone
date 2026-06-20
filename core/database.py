"""PostgreSQL connection pool using psycopg v3.

Connection details come from `core.config.Settings`. Supports:
- DATABASE_URL (preferred — every hosted Postgres provider emits this format)
- Discrete DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD (fallback for local dev)

Connection-time settings (TCP keepalives, ssl negotiation) were originally
tuned for WAN-attached Neon; production now runs Postgres locally on the same
VPS as the app, but the keepalives remain harmless and protect against any
future WAN-attached configuration.
"""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool

from core.config import get_settings

# Every connection in this codebase is opened with `row_factory=dict_row`, so
# rows are mappings (`row["col"]`, `row.get(...)`) rather than the psycopg
# default tuples. Parameterising the connection type with the row type teaches
# mypy that fact, which is what keeps the type-checker honest about row access
# across the repository and agent layers. `DictRow` is psycopg's alias for the
# `dict_row` factory's output.
DictConnection = psycopg.Connection[DictRow]

_pool: ConnectionPool[DictConnection] | None = None


def _pool_conninfo() -> str:
    """Build the conninfo string used for the pool.

    Prefers DATABASE_URL when set so any provider-specific query params
    (sslmode, channel_binding, etc.) pass through unchanged.
    """
    settings = get_settings()
    if settings.database_url:
        return settings.database_url
    return settings.psycopg_conninfo()


def init_pool(
    min_size: int = 2,
    max_size: int | None = None,
    timeout: float = 10.0,
) -> None:
    """Create the connection pool. Called at app startup.

    Pool size defaults to DB_POOL_MAX (env, default 15) — appropriate for local
    Postgres on a multi-core VPS where two app processes (api + web) share a
    DB with `max_connections=100`. Override via the env var or argument when
    sizing for a different surface.
    """
    global _pool
    effective_max = (
        max_size if max_size is not None else int(os.environ.get("DB_POOL_MAX", "15"))
    )
    _pool = ConnectionPool(
        conninfo=_pool_conninfo(),
        min_size=min_size,
        max_size=effective_max,
        timeout=timeout,
        open=True,
        kwargs={
            "row_factory": dict_row,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )


def close_pool() -> None:
    """Close the connection pool. Called at app shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def is_pool_initialized() -> bool:
    return _pool is not None


@contextmanager
def get_connection() -> Generator[DictConnection, None, None]:
    """Get a connection from the pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    with _pool.connection() as conn:
        yield conn


def get_db() -> Generator[DictConnection, None, None]:
    """FastAPI dependency that yields a database connection."""
    with get_connection() as conn:
        yield conn


def connect_one_shot() -> DictConnection:
    """Open a single connection without the pool.

    Used by CLI tools, migration scripts, and standalone connectors where
    opening a pool is overkill and adds startup latency.
    """
    settings = get_settings()
    conninfo = settings.database_url or settings.psycopg_conninfo()
    return psycopg.connect(conninfo, row_factory=dict_row)
