"""Shared pytest fixtures for Glintstone tests."""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def clean_env(monkeypatch):
    """Strip all GLINTSTONE/DB env vars and disable .env loading.

    Forces Settings() to use class defaults so tests don't depend on the
    developer's local `.env`.
    """
    for var in [
        "APP_ENV",
        "APP_DEBUG",
        "DATABASE_URL",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_SSLMODE",
        "API_PORT",
        "WEB_PORT",
        "MARKETING_PORT",
        "API_URL",
        "WEB_URL",
        "MARKETING_URL",
        "IMAGE_PATH",
        "DEPLOY_HOST",
        "ORCID_CLIENT_ID",
        "ORCID_CLIENT_SECRET",
        "ORCID_BASE_URL",
        "EMAIL_BACKEND",
        "SMTP_HOST",
        "SMTP_PORT",
        "RESEND_API_KEY",
        "EMAIL_FROM",
        "SESSION_SECRET_KEY",
        "SESSION_LIFETIME_DAYS",
    ]:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(ROOT / "tests")
    yield


@pytest.fixture
def has_database_url():
    """Skip integration tests if no DATABASE_URL is available."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Re-read settings the same way the app does (via .env in repo root)
        from core.config import get_settings, reset_settings_cache

        reset_settings_cache()
        url = get_settings().database_url
    if not url:
        pytest.skip("DATABASE_URL not set; integration test skipped")
    return url
