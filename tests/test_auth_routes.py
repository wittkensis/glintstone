"""Integration tests for auth + saved-items API routes.

Requires DATABASE_URL (skipped otherwise).
Uses respx to intercept outbound httpx calls for ORCID and Resend.
Covers scenarios from GitHub issue #76.

PRD-014 additions (TestInviteCodes, TestPasswordHashing, TestGenerateInviteScript):
  - invite_codes table CRUD via raw SQL (validates migration 044 schema)
  - password hash round-trip (documents expected auth_service interface)
  - invite code generation utility
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

    def test_session_lookup_returns_avatar_url(
        self, test_user, user_repo, session_repo, db_conn
    ):
        """Regression for #450: an avatar set on the user must survive a page
        reload. On reload the browser re-authenticates via the session cookie,
        so the session→user join is the read path. It previously dropped
        avatar_url (also role/theme), so the saved avatar vanished after refresh.
        """
        from datetime import datetime, timedelta, timezone
        from api.services.auth_service import generate_session_token, hash_token

        avatar_url = f"https://pub-test.r2.dev/avatars/{test_user['id']}.jpg"
        user_repo.update_avatar_url(test_user["id"], avatar_url)
        db_conn.commit()

        raw = generate_session_token()
        token_hash = hash_token(raw)
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        session_repo.create_session(test_user["id"], token_hash, expires_at)
        db_conn.commit()

        row = session_repo.find_by_token_hash(token_hash)
        assert row is not None
        # The read-back the middleware relies on must carry the persisted avatar.
        assert row["avatar_url"] == avatar_url
        # role + theme rode the same missing-column bug; assert they survive too.
        assert "role" in row
        assert "theme" in row

    def test_resolve_session_returns_only_ids(self, test_user, session_repo, db_conn):
        """#461: resolve_session returns just session_id + user_id (no user cols).

        The middleware uses this to get the user_id, then reloads the full users
        row via find_by_id — so the resolver intentionally carries no user
        columns and can never drop one.
        """
        from datetime import datetime, timedelta, timezone
        from api.services.auth_service import generate_session_token, hash_token

        raw = generate_session_token()
        token_hash = hash_token(raw)
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        session_repo.create_session(test_user["id"], token_hash, expires_at)
        db_conn.commit()

        sess = session_repo.resolve_session(token_hash)
        assert sess is not None
        assert str(sess["user_id"]) == str(test_user["id"])
        assert "session_id" in sess

    def test_resolve_session_expired_returns_none(
        self, test_user, session_repo, db_conn
    ):
        from datetime import datetime, timedelta, timezone
        from api.services.auth_service import generate_session_token, hash_token

        raw = generate_session_token()
        token_hash = hash_token(raw)
        past = datetime.now(timezone.utc) - timedelta(days=1)
        session_repo.create_session(test_user["id"], token_hash, past)
        db_conn.commit()

        assert session_repo.resolve_session(token_hash) is None

    def test_session_path_carries_full_user_row(
        self, test_user, user_repo, session_repo, db_conn
    ):
        """#461 regression: the session auth path must reflect the FULL users
        row, so any *future* users column is present without editing a
        hand-listed SELECT (the #450 class of bug, where avatar_url/role/theme
        silently dropped from the join).

        This reproduces exactly what the middleware does on the cookie/Bearer
        path: resolve the session to a user_id, then reload the whole row via
        find_by_id. We assert that EVERY column on the users table survives the
        round-trip — including columns this test was never written to know
        about — by diffing against the live table schema. Add a new users
        column tomorrow and this test guarantees the session path carries it
        with zero code changes to the auth path.
        """
        from datetime import datetime, timedelta, timezone
        from api.services.auth_service import generate_session_token, hash_token
        from api.middleware.auth import _load_session_user

        raw = generate_session_token()
        token_hash = hash_token(raw)
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        session_repo.create_session(test_user["id"], token_hash, expires_at)
        db_conn.commit()

        # What the middleware actually builds for request.state.user.
        loaded = _load_session_user(db_conn, token_hash)
        assert loaded is not None
        assert str(loaded["id"]) == str(test_user["id"])
        assert loaded["session_id"] is not None

        # The columns that #450 added back by hand must still be present...
        for col in (
            "email",
            "display_name",
            "orcid_id",
            "email_verified_at",
            "avatar_url",
            "role",
            "theme",
        ):
            assert col in loaded, f"#450/#461 regression: '{col}' dropped"

        # ...AND every other users column, discovered from the live schema, so a
        # future column can never silently drop on the session path again.
        with db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users'
                """
            )
            all_user_columns = {r["column_name"] for r in cur.fetchall()}
        missing = all_user_columns - set(loaded.keys())
        assert not missing, (
            f"#461 regression: session path dropped users columns {missing}. "
            "The session auth path must reload the full users row (find_by_id) "
            "so new columns appear automatically."
        )


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


# ── PRD-014: invite codes ─────────────────────────────────────────────────────


@pytest.fixture
def test_invite_code(db_conn):
    """Insert a fresh unused invite code; rolled back after each test."""
    with db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO invite_codes (code, label) VALUES (%s, %s) RETURNING *",
            ("TEST-UNIT-CODE", "pytest fixture"),
        )
        row = cur.fetchone()
    db_conn.commit()
    return row


class TestInviteCodes:
    """Tests for the invite_codes table added in migration 044.

    Uses raw SQL because no InviteCodeRepository exists yet — the repo
    lives in api/routes/auth.py (separate worker scope). These tests
    validate the schema and query patterns the API will use.
    """

    def test_insert_and_find_code(self, db_conn):
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO invite_codes (code, label) VALUES (%s, %s) RETURNING *",
                ("ABCD-EFGH-IJKL", "test batch"),
            )
            row = cur.fetchone()
        db_conn.commit()

        assert row is not None
        assert row["code"] == "ABCD-EFGH-IJKL"
        assert row["label"] == "test batch"
        assert row["used_at"] is None
        assert row["used_by_email"] is None

    def test_code_uniqueness_constraint(self, db_conn):
        """Duplicate invite codes must be rejected by the DB."""
        import psycopg

        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO invite_codes (code) VALUES (%s)",
                ("DUPL-ICAT-CODE",),
            )
        db_conn.commit()

        with pytest.raises(psycopg.errors.UniqueViolation):
            with db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO invite_codes (code) VALUES (%s)",
                    ("DUPL-ICAT-CODE",),
                )
            db_conn.commit()

    def test_mark_code_used(self, test_invite_code, db_conn):
        """Marking a code used records email and timestamp."""
        with db_conn.cursor() as cur:
            cur.execute(
                """
                UPDATE invite_codes
                   SET used_by_email = %s, used_at = now()
                 WHERE id = %s
                """,
                ("scholar@university.edu", test_invite_code["id"]),
            )
        db_conn.commit()

        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM invite_codes WHERE id = %s",
                (test_invite_code["id"],),
            )
            row = cur.fetchone()

        assert row["used_by_email"] == "scholar@university.edu"
        assert row["used_at"] is not None

    def test_unused_code_query(self, test_invite_code, db_conn):
        """An unused code can be found by code string with used_at IS NULL guard."""
        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM invite_codes WHERE code = %s AND used_at IS NULL",
                (test_invite_code["code"],),
            )
            row = cur.fetchone()
        assert row is not None
        assert row["id"] == test_invite_code["id"]

    def test_used_code_not_returned_as_available(self, test_invite_code, db_conn):
        """Once marked used, the code does not appear in available queries."""
        with db_conn.cursor() as cur:
            cur.execute(
                "UPDATE invite_codes SET used_by_email = %s, used_at = now() WHERE id = %s",
                ("someone@example.com", test_invite_code["id"]),
            )
        db_conn.commit()

        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM invite_codes WHERE code = %s AND used_at IS NULL",
                (test_invite_code["code"],),
            )
            row = cur.fetchone()
        assert row is None

    def test_users_table_has_password_columns(self, user_repo, db_conn):
        """Migration 044 added password_hash, name, affiliation, invite_code_id to users."""
        user_repo.create_user(email="pwcol-check@glintstone.example")
        db_conn.commit()
        row = user_repo.find_by_email("pwcol-check@glintstone.example")
        assert row is not None
        for col in ("password_hash", "name", "affiliation", "invite_code_id"):
            assert col in row, (
                f"Column '{col}' missing from users table — run migration 044"
            )


# ── PRD-014: password hashing ─────────────────────────────────────────────────


class TestPasswordHashing:
    """Documents the expected hash_password / verify_password interface.

    These functions must be added to api/services/auth_service.py by the
    API-side worker. If they don't exist, these tests fail with ImportError —
    that failure is intentional and serves as the integration gate.
    """

    def test_hash_is_not_plaintext(self):
        from api.services.auth_service import hash_password

        h = hash_password("correcthorsebatterystaple")
        assert h != "correcthorsebatterystaple"
        assert len(h) > 20

    def test_verify_correct_password(self):
        from api.services.auth_service import hash_password, verify_password

        pw = "openbarley42"
        h = hash_password(pw)
        assert verify_password(pw, h) is True

    def test_verify_wrong_password(self):
        from api.services.auth_service import hash_password, verify_password

        h = hash_password("rightpassword")
        assert verify_password("wrongpassword", h) is False

    def test_hashes_are_unique_per_call(self):
        """Each call to hash_password produces a unique hash (random salt)."""
        from api.services.auth_service import hash_password

        pw = "samepassword"
        assert hash_password(pw) != hash_password(pw)


# ── PRD-014: invite code generator (pure unit — no DB) ───────────────────────


class TestGenerateInviteScript:
    def test_generate_code_format(self):
        """Generated codes are in XXXX-XXXX-XXXX format."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "generate_invite",
            str(ROOT / "ops" / "tools" / "generate_invite.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        code = mod.generate_code()
        parts = code.split("-")
        assert len(parts) == 3
        assert all(len(p) == 4 for p in parts)
        assert all(c.isalnum() for p in parts for c in p)

    def test_codes_are_unique(self):
        """10 generated codes should all be distinct."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "generate_invite",
            str(ROOT / "ops" / "tools" / "generate_invite.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        codes = {mod.generate_code() for _ in range(10)}
        assert len(codes) == 10

    def test_no_ambiguous_chars(self):
        """Codes must not contain O, 0, I, or 1 (visually ambiguous)."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "generate_invite",
            str(ROOT / "ops" / "tools" / "generate_invite.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for _ in range(50):
            code = mod.generate_code().replace("-", "")
            for ambiguous in ("O", "0", "I", "1"):
                assert ambiguous not in code, (
                    f"Ambiguous char '{ambiguous}' found in {code}"
                )
