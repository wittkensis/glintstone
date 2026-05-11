"""PostgreSQL connection pool using psycopg v3.

Connection details come from `core.config.Settings`. Supports:
- DATABASE_URL (preferred — Neon, Railway, Supabase, RDS all emit this format)
- Discrete DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD (fallback for local dev)

Connection-time settings (TCP keepalives, ssl negotiation) are tuned for hosted
Postgres providers like Neon that benefit from explicit keepalives over WAN.
"""

from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from core.config import get_settings

_pool: ConnectionPool | None = None


def _pool_conninfo() -> str:
    """Build the conninfo string used for the pool.

    Prefers DATABASE_URL when set so any provider-specific query params
    (sslmode, channel_binding, etc.) pass through unchanged.
    """
    settings = get_settings()
    if settings.database_url:
        return settings.database_url
    return settings.psycopg_conninfo()


def init_pool(min_size: int = 0, max_size: int = 5, timeout: float = 10.0) -> None:
    """Create the connection pool. Called at app startup."""
    global _pool
    _pool = ConnectionPool(
        conninfo=_pool_conninfo(),
        min_size=min_size,
        max_size=max_size,
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
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Get a connection from the pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    with _pool.connection() as conn:
        yield conn


def get_db() -> Generator[psycopg.Connection, None, None]:
    """FastAPI dependency that yields a database connection."""
    with get_connection() as conn:
        yield conn


def connect_one_shot() -> psycopg.Connection:
    """Open a single connection without the pool.

    Used by CLI tools, migration scripts, and standalone connectors where
    opening a pool is overkill and adds startup latency.
    """
    settings = get_settings()
    conninfo = settings.database_url or settings.psycopg_conninfo()
    return psycopg.connect(conninfo, row_factory=dict_row)
