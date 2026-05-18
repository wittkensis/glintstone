"""Integration tests for auth + saved-items API routes.

Requires DATABASE_URL (skipped otherwise).
Uses respx to intercept outbound httpx calls for ORCID and Resend.
Covers scenarios from GitHub issue #76.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def db_conn(has_database_url):
    """A psycopg connection per test; rolled back after each test."""
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(has_database_url, row_factory=dict_row)
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def user_repo(db_conn):
    from api.repositories.user_repo import UserRepository

    return UserRepository(db_conn)


@pytest.fixture
def session_repo(db_conn):
    from api.repositories.session_repo import SessionRepository

    return SessionRepository(db_conn)


@pytest.fixture
def api_key_repo(db_conn):
    from api.repositories.api_key_repo import ApiKeyRepository

    return ApiKeyRepository(db_conn)


@pytest.fixture
def saved_items_repo(db_conn):
    from api.repositories.saved_items_repo import SavedItemsRepository

    return SavedItemsRepository(db_conn)


@pytest.fixture
def test_user(user_repo, db_conn):
    user = user_repo.create_user(
        email="test-auth@glintstone.example",
        display_name="Test Scholar",
    )
    user_repo.link_auth_method(user["id"], "magic_link", "test-auth@glintstone.example")
    db_conn.commit()
    return user


@pytest.fixture
def test_session(test_user, session_repo, db_conn):
    from datetime import datetime, timedelta, timezone
    from api.services.auth_service import generate_session_token, hash_token

    raw = generate_session_token()
    token_hash = hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    session_repo.create_session(
        user_id=test_user["id"],
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db_conn.commit()
    return raw  # raw bearer token


# ── Repository unit-level integration tests ───────────────────────────────────


class TestUserRepo:
    def test_create_and_find_by_email(self, user_repo, db_conn):
        user_repo.create_user(email="new@example.com", display_name="New")
        db_conn.commit()
        found = user_repo.find_by_email("new@example.com")
        assert found is not None
        assert found["display_name"] == "New"

    def test_create_upserts_on_conflict(self, user_repo, db_conn):
        user_repo.create_user(email="dup@example.com")
        db_conn.commit()
        user_repo.create_user(email="dup@example.com", display_name="Updated")
        db_conn.commit()
        found = user_repo.find_by_email("dup@example.com")
        assert found["display_name"] == "Updated"

    def test_find_by_provider(self, test_user, user_repo):
        found = user_repo.find_by_provider("magic_link", "test-auth@glintstone.example")
        assert found is not None
        assert found["id"] == test_user["id"]

    def test_find_by_provider_missing(self, user_repo):
        assert user_repo.find_by_provider("orcid", "0000-9999-9999-9999") is None


class TestSessionRepo:
    def test_create_and_find(self, test_user, session_repo, db_conn):
        from datetime import datetime, timedelta, timezone
        from api.services.auth_service import generate_session_token, hash_token

        raw = generate_session_token()
        token_hash = hash_token(raw)
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        session_repo.create_session(test_user["id"], token_hash, expires_at)
        db_conn.commit()

        row = session_repo.find_by_token_hash(token_hash)
        assert row is not None
        assert row["email"] == test_user["email"]

    def test_revoke(self, test_user, session_repo, db_conn):
        from datetime import datetime, timedelta, timezone
        from api.services.auth_service import generate_session_token, hash_token

        raw = generate_session_token()
        token_hash = hash_token(raw)
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        session = session_repo.create_session(test_user["id"], token_hash, expires_at)
        db_conn.commit()

        session_repo.revoke(session["id"])
        db_conn.commit()

        assert session_repo.find_by_token_hash(token_hash) is None

    def test_expired_session_not_returned(self, test_user, session_repo, db_conn):
        from datetime import datetime, timedelta, timezone
        from api.services.auth_service import generate_session_token, hash_token

        raw = generate_session_token()
        token_hash = hash_token(raw)
        past = datetime.now(timezone.utc) - timedelta(days=1)
        session_repo.create_session(test_user["id"], token_hash, past)
        db_conn.commit()

        assert session_repo.find_by_token_hash(token_hash) is None


class TestApiKeyRepo:
    def test_create_and_find(self, test_user, api_key_repo, db_conn):
        from api.services.auth_service import generate_api_key

        raw, key_hash = generate_api_key()
        api_key_repo.create(test_user["id"], key_hash, "test key")
        db_conn.commit()

        row = api_key_repo.find_by_hash(key_hash)
        assert row is not None
        assert row["user_id"] == test_user["id"]

    def test_revoked_key_not_found(self, test_user, api_key_repo, db_conn):
        from api.services.auth_service import generate_api_key

        raw, key_hash = generate_api_key()
        row = api_key_repo.create(test_user["id"], key_hash, "revokable")
        db_conn.commit()

        api_key_repo.revoke(str(row["id"]), str(test_user["id"]))
        db_conn.commit()

        assert api_key_repo.find_by_hash(key_hash) is None

    def test_revoke_wrong_user_returns_false(
        self, test_user, user_repo, api_key_repo, db_conn
    ):
        import uuid
        from api.services.auth_service import generate_api_key

        raw, key_hash = generate_api_key()
        row = api_key_repo.create(test_user["id"], key_hash, "mine")
        db_conn.commit()

        other_id = str(uuid.uuid4())
        revoked = api_key_repo.revoke(str(row["id"]), other_id)
        assert revoked is False


class TestSavedItemsRepo:
    def test_save_and_list(self, test_user, saved_items_repo, db_conn):
        saved_items_repo.save(test_user["id"], "artifact", "P123456")
        db_conn.commit()

        items = saved_items_repo.list_for_user(test_user["id"], "artifact")
        assert any(i["item_id"] == "P123456" for i in items)

    def test_save_idempotent(self, test_user, saved_items_repo, db_conn):
        saved_items_repo.save(test_user["id"], "artifact", "P111111")
        db_conn.commit()
        saved_items_repo.save(test_user["id"], "artifact", "P111111")
        db_conn.commit()
        saved_items_repo.save(test_user["id"], "artifact", "P111111")
        db_conn.commit()

        items = saved_items_repo.list_for_user(test_user["id"], "artifact")
        assert sum(1 for i in items if i["item_id"] == "P111111") == 1

    def test_delete(self, test_user, saved_items_repo, db_conn):
        row = saved_items_repo.save(test_user["id"], "artifact", "P999999")
        db_conn.commit()

        deleted = saved_items_repo.delete(str(row["id"]), str(test_user["id"]))
        db_conn.commit()
        assert deleted is True

        items = saved_items_repo.list_for_user(test_user["id"], "artifact")
        assert not any(i["item_id"] == "P999999" for i in items)

    def test_delete_not_found(self, test_user, saved_items_repo):
        import uuid

        deleted = saved_items_repo.delete(str(uuid.uuid4()), str(test_user["id"]))
        assert deleted is False
