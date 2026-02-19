"""PostgreSQL connection pool using psycopg v3."""

from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from glintstone.config import get_settings

_pool: ConnectionPool | None = None


def init_pool() -> None:
    """Create the connection pool. Called at app startup."""
    global _pool
    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} "
        f"port={settings.db_port} "
        f"dbname={settings.db_name} "
        f"user={settings.db_user} "
        f"password={settings.db_password}"
    )
    _pool = ConnectionPool(
        conninfo=conninfo,
        min_size=0,
        max_size=5,
        timeout=5,
        kwargs={"row_factory": dict_row},
    )


def close_pool() -> None:
    """Close the connection pool. Called at app shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


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
