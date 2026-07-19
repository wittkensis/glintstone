"""Regression tests for the 2026-07-17 QA review (see _QA-REVIEW-2026-07-17.md).

Pins the fixes so they cannot silently regress:

- BUG-1: HEAD requests on the app probes (/healthz, /version) return 200, not
  405. The QA report noted a single HEAD assertion would have caught this.
- BUG-5: the login page exposes a password field and a native POST to
  /auth/login, so a password set at registration has a working UI path.
- BUG-6: an unauthenticated /favicon.ico request returns 204 and is NOT
  redirected to /auth/login by the auth gate.

These are unit-level tests against the ASGI app; they do not need a database.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _StubTransport:
    def get(self, path, params=None, token=None):
        return {}

    def post(self, path, json=None, token=None):
        return {}

    def put(self, path, json=None, token=None):
        return {}

    def patch(self, path, json=None, token=None):
        return None

    def delete(self, path, token=None):
        return None

    def close(self):
        pass


@pytest.fixture
def anon_client(monkeypatch):
    """App client with NO session cookie (unauthenticated) and no real DB."""
    from core import database

    monkeypatch.setattr(database, "init_pool", lambda *a, **kw: None)
    monkeypatch.setattr(database, "close_pool", lambda *a, **kw: None)

    from app import main as app_main
    from app.api_client import GlintstoneAPI
    from app.transports import HttpxTransport

    monkeypatch.setattr(HttpxTransport, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(HttpxTransport, "close", lambda self: None)

    fake_api = GlintstoneAPI(_StubTransport())
    # follow_redirects=False so we can assert on the 302 the auth gate would emit.
    with TestClient(app_main.app, follow_redirects=False) as c:
        c.app.state.api = fake_api
        yield c


# ── BUG-1: HEAD on probes ──────────────────────────────────────────────────


@pytest.mark.parametrize("path", ["/healthz", "/version"])
def test_head_probe_returns_200(anon_client, path):
    assert anon_client.head(path).status_code == 200


@pytest.mark.parametrize("path", ["/healthz", "/version"])
def test_get_probe_still_returns_200(anon_client, path):
    assert anon_client.get(path).status_code == 200


# ── BUG-6: favicon ─────────────────────────────────────────────────────────


def test_favicon_ico_returns_204_no_redirect(anon_client):
    resp = anon_client.get("/favicon.ico")
    assert resp.status_code == 204
    # Must NOT have been redirected to the login page by the auth gate.
    assert "location" not in {k.lower() for k in resp.headers}


def test_favicon_ico_head_ok(anon_client):
    assert anon_client.head("/favicon.ico").status_code == 204


def test_gated_route_still_redirects_when_anonymous(anon_client):
    """Guard: opening favicon/probes did not weaken the auth gate."""
    resp = anon_client.get("/tablets")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login"


# ── BUG-5: login page has a password path ──────────────────────────────────


def test_login_page_has_password_field_and_native_post(anon_client):
    html = anon_client.get("/auth/login").text
    assert 'type="password"' in html
    assert 'name="password"' in html
    assert 'action="/auth/login"' in html
    assert 'method="post"' in html
    # Magic-link fallback is preserved.
    assert "Email me a sign-in link instead" in html
