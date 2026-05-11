"""Tests for core.config.Settings — DATABASE_URL parsing, env routing, fallback."""

import importlib

import pytest


def _fresh_settings():
    """Re-import core.config so it picks up env changes since conftest fixture."""
    from core import config as _config

    importlib.reload(_config)
    return _config.Settings()


def test_defaults_when_no_env(clean_env):
    s = _fresh_settings()
    assert s.app_env == "local"
    assert s.db_host == "127.0.0.1"
    assert s.db_port == 5432
    assert s.db_name == "glintstone"
    assert s.db_user == "glintstone"
    assert s.database_url is None
    assert s.db_sslmode is None


def test_discrete_db_vars_override_defaults(clean_env, monkeypatch):
    monkeypatch.setenv("DB_HOST", "example.com")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "mydb")
    monkeypatch.setenv("DB_USER", "alice")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    s = _fresh_settings()
    assert s.db_host == "example.com"
    assert s.db_port == 6543
    assert s.db_name == "mydb"
    assert s.db_user == "alice"
    assert s.db_password == "secret"


def test_database_url_backfills_discrete_fields(clean_env, monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://alice:s3cret@db.example.com:5433/widgets?sslmode=require",
    )
    s = _fresh_settings()
    assert s.database_url is not None
    assert s.db_host == "db.example.com"
    assert s.db_port == 5433
    assert s.db_name == "widgets"
    assert s.db_user == "alice"
    assert s.db_password == "s3cret"
    assert s.db_sslmode == "require"


def test_database_url_takes_precedence_over_discrete(clean_env, monkeypatch):
    monkeypatch.setenv("DB_HOST", "should-be-ignored.com")
    monkeypatch.setenv("DB_NAME", "should-be-ignored")
    monkeypatch.setenv("DATABASE_URL", "postgres://bob:pw@real.example.com:5432/proddb")
    s = _fresh_settings()
    assert s.db_host == "real.example.com"
    assert s.db_name == "proddb"
    assert s.db_user == "bob"


def test_database_url_postgres_scheme_accepted(clean_env, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h:5432/d")
    s = _fresh_settings()
    assert s.db_host == "h"


def test_database_url_invalid_scheme_rejected(clean_env, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql://u:p@h:3306/d")
    with pytest.raises(Exception):
        _fresh_settings()


def test_database_url_missing_host_rejected(clean_env, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql:///dbname")
    with pytest.raises(Exception):
        _fresh_settings()


def test_effective_database_url_from_discrete(clean_env, monkeypatch):
    monkeypatch.setenv("DB_HOST", "x.com")
    monkeypatch.setenv("DB_PORT", "1234")
    monkeypatch.setenv("DB_NAME", "d")
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")
    monkeypatch.setenv("DB_SSLMODE", "prefer")
    s = _fresh_settings()
    url = s.effective_database_url()
    assert url == "postgresql://u:p@x.com:1234/d?sslmode=prefer"


def test_effective_database_url_returns_url_when_set(clean_env, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:5432/d?sslmode=require")
    s = _fresh_settings()
    assert s.effective_database_url() == "postgresql://u:p@h:5432/d?sslmode=require"


def test_psycopg_conninfo_includes_sslmode(clean_env, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:5432/d?sslmode=require")
    s = _fresh_settings()
    conninfo = s.psycopg_conninfo()
    assert "host=h" in conninfo
    assert "port=5432" in conninfo
    assert "dbname=d" in conninfo
    assert "user=u" in conninfo
    assert "password=p" in conninfo
    assert "sslmode=require" in conninfo


def test_psycopg_conninfo_omits_sslmode_when_unset(clean_env, monkeypatch):
    monkeypatch.setenv("DB_HOST", "h")
    s = _fresh_settings()
    assert "sslmode=" not in s.psycopg_conninfo()


def test_app_env_default_is_local(clean_env):
    s = _fresh_settings()
    assert s.app_env == "local"


def test_app_env_override(clean_env, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    s = _fresh_settings()
    assert s.app_env == "production"
