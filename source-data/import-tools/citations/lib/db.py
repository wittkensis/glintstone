"""
Shared PostgreSQL connection factory for citation pipeline scripts.

All scripts use this instead of hardcoded sqlite3 connections.
Connection settings come from core.config.get_settings().
"""

import sys
from pathlib import Path

# Add project root to path so core package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import psycopg

from core.config import get_settings


def get_connection(row_factory=None) -> psycopg.Connection:
    """Return a psycopg connection using project settings.

    Args:
        row_factory: Optional row factory (e.g. dict_row for dict results).
                     Default is tuple rows.
    """
    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} "
        f"port={settings.db_port} "
        f"dbname={settings.db_name} "
        f"user={settings.db_user} "
        f"password={settings.db_password}"
    )
    kwargs = {}
    if row_factory:
        kwargs["row_factory"] = row_factory
    return psycopg.connect(conninfo, **kwargs)


def get_conninfo() -> str:
    """Return the connection string for cases needing raw conninfo."""
    settings = get_settings()
    return (
        f"host={settings.db_host} "
        f"port={settings.db_port} "
        f"dbname={settings.db_name} "
        f"user={settings.db_user} "
        f"password={settings.db_password}"
    )
