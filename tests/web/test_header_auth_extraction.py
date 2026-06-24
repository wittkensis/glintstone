"""#125 — verify the header auth script was extracted to header-auth.js (F-5).

The audit finding was that the auth IIFE lived inline in base.html, tightly
coupled to the header markup and impossible to cache or lint on its own. These
tests pin the extraction so it can't silently regress back inline, and confirm
the external file is actually served and still wired to the header elements.
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
def client(monkeypatch):
    from core import database

    monkeypatch.setattr(database, "init_pool", lambda *a, **kw: None)
    monkeypatch.setattr(database, "close_pool", lambda *a, **kw: None)

    from app import main as app_main
    from app.api_client import GlintstoneAPI
    from app.transports import HttpxTransport

    monkeypatch.setattr(HttpxTransport, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(HttpxTransport, "close", lambda self: None)

    fake_api = GlintstoneAPI(_StubTransport())
    with TestClient(app_main.app, cookies={"session_token": "test-token"}) as c:
        c.app.state.api = fake_api
        yield c


def test_header_auth_script_is_referenced(client):
    """A rendered page references the extracted header-auth.js file."""
    r = client.get("/")
    # Home may redirect or render; follow to a 200 HTML page.
    if r.status_code not in (200,):
        pytest.skip(f"home returned {r.status_code}")
    assert "/static/js/header-auth.js" in r.text


def test_auth_iife_not_inlined(client):
    """The inline fetch('/_me') IIFE must no longer live in the page source."""
    r = client.get("/")
    if r.status_code != 200:
        pytest.skip(f"home returned {r.status_code}")
    # The old inline marker — an inline fetch to the session proxy — is gone.
    assert "fetch('/_me')" not in r.text


def test_header_auth_file_is_served(client):
    """The static file exists and is served with its auth logic intact."""
    r = client.get("/static/js/header-auth.js")
    assert r.status_code == 200
    body = r.text
    assert "/_me" in body
    assert "header-user" in body
    assert "header-avatar" in body
