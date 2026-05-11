"""Tests for core.database — pool lifecycle and one-shot connections.

The integration tests in this module require a real DATABASE_URL and will be
skipped if one is not set. Unit-only tests run against an unset pool to verify
error paths.
"""

import importlib

import pytest


def _fresh_db_module():
    """Reload core.database with current env state."""
    from core import config, database

    importlib.reload(config)
    importlib.reload(database)
    return database


def test_get_connection_errors_when_pool_uninitialized(clean_env):
    db = _fresh_db_module()
    db.close_pool()
    assert not db.is_pool_initialized()
    with pytest.raises(RuntimeError, match="not initialized"):
        with db.get_connection():
            pass


def test_pool_lifecycle_init_and_close(has_database_url):
    db = _fresh_db_module()
    db.close_pool()
    db.init_pool(min_size=0, max_size=2)
    assert db.is_pool_initialized()
    with db.get_connection() as conn:
        row = conn.execute("SELECT 1 AS v").fetchone()
        assert row["v"] == 1
    db.close_pool()
    assert not db.is_pool_initialized()


def test_connect_one_shot_returns_usable_connection(has_database_url):
    db = _fresh_db_module()
    conn = db.connect_one_shot()
    try:
        row = conn.execute("SELECT 1 AS v").fetchone()
        assert row["v"] == 1
    finally:
        conn.close()


def test_pool_returns_dict_rows(has_database_url):
    db = _fresh_db_module()
    db.close_pool()
    db.init_pool(min_size=0, max_size=2)
    try:
        with db.get_connection() as conn:
            row = conn.execute("SELECT 1 AS one, 'x' AS letter").fetchone()
            assert row["one"] == 1
            assert row["letter"] == "x"
    finally:
        db.close_pool()
