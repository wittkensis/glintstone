"""Integration tests for the Scholar Identity feature (#17).

DB-backed (skipped without DATABASE_URL; runs in CI per #470). Validates
migration 060's schema and the claim/overlay invariants the feature hinges on:

  - the claim lifecycle (pending → approved / rejected);
  - the partial unique index enforcing ONE approved claim per scholar;
  - a user can't file two pending claims on the same scholar;
  - the scholar_overrides COALESCE read model (overlay wins, reverts on delete);
  - the bio-edit authorization guard (only the approved claimant);
  - admin-gating of the verify/queue routes (403 for a standard user);
  - no auth regression (a magic-link user still authenticates).

These reuse the db_conn / user_repo / test_user fixtures from test_auth_routes.py
(same package, so pytest discovers them via the shared conftest + that module's
fixtures are imported below for clarity).
"""

import uuid

import psycopg
import pytest

pytestmark = pytest.mark.usefixtures("has_database_url")


@pytest.fixture
def db_conn(has_database_url):
    from psycopg.rows import dict_row

    conn = psycopg.connect(has_database_url, row_factory=dict_row)
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def a_user(db_conn):
    """A fresh user with an ORCID, cleaned up on teardown (claims cascade)."""
    from api.repositories.user_repo import UserRepository

    repo = UserRepository(db_conn)
    email = f"claim-test-{uuid.uuid4().hex[:8]}@glintstone.example"
    user = repo.create_user(
        email=email,
        display_name="Claim Tester",
        orcid_id=f"0000-0001-{uuid.uuid4().hex[:4]}-0000",
    )
    db_conn.commit()
    yield user
    with db_conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user["id"],))
    db_conn.commit()


@pytest.fixture
def another_user(db_conn):
    from api.repositories.user_repo import UserRepository

    repo = UserRepository(db_conn)
    email = f"claim-test2-{uuid.uuid4().hex[:8]}@glintstone.example"
    user = repo.create_user(email=email, display_name="Second Tester")
    db_conn.commit()
    yield user
    with db_conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user["id"],))
    db_conn.commit()


@pytest.fixture
def a_scholar(db_conn):
    """A throwaway scholar row (so claim FKs resolve), removed on teardown."""
    with db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO scholars (name, institution, expertise_periods) "
            "VALUES (%s, %s, %s) RETURNING id",
            ("Test, Scholar", "Ingested University", "Ur III"),
        )
        sid = cur.fetchone()["id"]
    db_conn.commit()
    yield sid
    with db_conn.cursor() as cur:
        cur.execute("DELETE FROM scholars WHERE id = %s", (sid,))
    db_conn.commit()


class TestSchema060:
    def test_tables_exist(self, db_conn):
        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_name IN ('scholar_claims', 'scholar_overrides')"
            )
            names = {r["table_name"] for r in cur.fetchall()}
        assert names == {"scholar_claims", "scholar_overrides"}, (
            "Run migration 060 — scholar_claims / scholar_overrides missing"
        )


class TestClaimLifecycle:
    def test_pending_then_approve_creates_overlay_shell(
        self, db_conn, a_user, a_scholar
    ):
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO scholar_claims
                    (user_id, scholar_id, status, verification_method, claim_note)
                VALUES (%s, %s, 'pending', 'manual_review', %s)
                RETURNING id, status
                """,
                (a_user["id"], a_scholar, "I am the author"),
            )
            claim = cur.fetchone()
            assert claim["status"] == "pending"

            # Approve: mirror the admin route's side effects.
            cur.execute(
                "UPDATE scholar_claims SET status='approved', verified_at=now() "
                "WHERE id = %s",
                (claim["id"],),
            )
            cur.execute(
                "INSERT INTO scholar_overrides (scholar_id, edited_by_user_id) "
                "VALUES (%s, %s) ON CONFLICT (scholar_id) DO NOTHING",
                (a_scholar, a_user["id"]),
            )
            cur.execute(
                "SELECT 1 FROM scholar_overrides WHERE scholar_id = %s", (a_scholar,)
            )
            assert cur.fetchone() is not None
        db_conn.commit()

    def test_reject_records_reason(self, db_conn, a_user, a_scholar):
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scholar_claims "
                "(user_id, scholar_id, status, verification_method) "
                "VALUES (%s, %s, 'pending', 'manual_review') RETURNING id",
                (a_user["id"], a_scholar),
            )
            cid = cur.fetchone()["id"]
            cur.execute(
                "UPDATE scholar_claims SET status='rejected', review_note=%s "
                "WHERE id = %s",
                ("Cannot verify identity", cid),
            )
            cur.execute(
                "SELECT status, review_note FROM scholar_claims WHERE id=%s", (cid,)
            )
            row = cur.fetchone()
        assert row["status"] == "rejected"
        assert row["review_note"] == "Cannot verify identity"
        db_conn.rollback()


class TestOneApprovedClaimPerScholar:
    def test_partial_unique_index_blocks_second_approved(
        self, db_conn, a_user, another_user, a_scholar
    ):
        """The load-bearing invariant: only one approved claim per scholar."""
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scholar_claims "
                "(user_id, scholar_id, status, verification_method) "
                "VALUES (%s, %s, 'approved', 'orcid_match')",
                (a_user["id"], a_scholar),
            )
        db_conn.commit()

        with pytest.raises(psycopg.errors.UniqueViolation):
            with db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO scholar_claims "
                    "(user_id, scholar_id, status, verification_method) "
                    "VALUES (%s, %s, 'approved', 'manual_review')",
                    (another_user["id"], a_scholar),
                )
            db_conn.commit()
        db_conn.rollback()

    def test_two_pending_by_same_user_blocked(self, db_conn, a_user, a_scholar):
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scholar_claims "
                "(user_id, scholar_id, status, verification_method) "
                "VALUES (%s, %s, 'pending', 'manual_review')",
                (a_user["id"], a_scholar),
            )
        db_conn.commit()
        with pytest.raises(psycopg.errors.UniqueViolation):
            with db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO scholar_claims "
                    "(user_id, scholar_id, status, verification_method) "
                    "VALUES (%s, %s, 'pending', 'manual_review')",
                    (a_user["id"], a_scholar),
                )
            db_conn.commit()
        db_conn.rollback()

    def test_rejected_does_not_block_reclaim(self, db_conn, a_user, a_scholar):
        """A rejected row must not block a fresh pending attempt (re-claim allowed)."""
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scholar_claims "
                "(user_id, scholar_id, status, verification_method) "
                "VALUES (%s, %s, 'rejected', 'manual_review')",
                (a_user["id"], a_scholar),
            )
            # A new pending claim by the same user on the same scholar is fine.
            cur.execute(
                "INSERT INTO scholar_claims "
                "(user_id, scholar_id, status, verification_method) "
                "VALUES (%s, %s, 'pending', 'manual_review') RETURNING id",
                (a_user["id"], a_scholar),
            )
            assert cur.fetchone()["id"] is not None
        db_conn.rollback()


class TestOverlayCoalesce:
    def test_overlay_wins_and_reverts_on_delete(self, db_conn, a_user, a_scholar):
        """COALESCE(override, ingested): overlay value wins; deleting it reverts."""
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scholar_overrides "
                "(scholar_id, edited_by_user_id, institution, bio) "
                "VALUES (%s, %s, %s, %s)",
                (a_scholar, a_user["id"], "Overlay University", "A bio."),
            )
            cur.execute(
                """
                SELECT COALESCE(o.institution, s.institution) AS institution, o.bio
                FROM scholars s
                LEFT JOIN scholar_overrides o ON o.scholar_id = s.id
                WHERE s.id = %s
                """,
                (a_scholar,),
            )
            row = cur.fetchone()
            assert row["institution"] == "Overlay University"
            assert row["bio"] == "A bio."

            # Delete the overlay → reverts to the ingested institution.
            cur.execute(
                "DELETE FROM scholar_overrides WHERE scholar_id = %s", (a_scholar,)
            )
            cur.execute(
                """
                SELECT COALESCE(o.institution, s.institution) AS institution
                FROM scholars s
                LEFT JOIN scholar_overrides o ON o.scholar_id = s.id
                WHERE s.id = %s
                """,
                (a_scholar,),
            )
            assert cur.fetchone()["institution"] == "Ingested University"
        db_conn.rollback()


class TestBioEditGuard:
    def test_only_approved_claimant_passes_guard(
        self, db_conn, a_user, another_user, a_scholar
    ):
        """The guard query the bio-edit route runs: SELECT 1 WHERE approved claim."""
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scholar_claims "
                "(user_id, scholar_id, status, verification_method) "
                "VALUES (%s, %s, 'approved', 'orcid_match')",
                (a_user["id"], a_scholar),
            )

            def has_claim(user_id):
                cur.execute(
                    "SELECT 1 FROM scholar_claims "
                    "WHERE scholar_id = %s AND user_id = %s AND status = 'approved'",
                    (a_scholar, user_id),
                )
                return cur.fetchone() is not None

            assert has_claim(a_user["id"]) is True
            assert has_claim(another_user["id"]) is False
        db_conn.rollback()


class TestAdminGating:
    """The admin verify/queue routes must reject a standard user (#461 role)."""

    def test_require_admin_rejects_standard_user(self):
        from fastapi import HTTPException
        from api.dependencies import require_admin

        class _Req:
            class state:
                user = {"id": "u1", "role": "standard"}

        with pytest.raises(HTTPException) as exc:
            require_admin(_Req())
        assert exc.value.status_code == 403

    def test_require_admin_allows_admin(self):
        from api.dependencies import require_admin

        class _Req:
            class state:
                user = {"id": "u1", "role": "admin"}

        assert require_admin(_Req())["role"] == "admin"

    def test_require_admin_rejects_anonymous(self):
        from fastapi import HTTPException
        from api.dependencies import require_admin

        class _Req:
            class state:
                user = None

        with pytest.raises(HTTPException) as exc:
            require_admin(_Req())
        assert exc.value.status_code == 401


class TestNoAuthRegression:
    """The claim feature must not break the existing magic-link path."""

    def test_magic_link_user_still_authenticates(self, db_conn):
        from api.repositories.user_repo import UserRepository
        from api.repositories.session_repo import SessionRepository
        from api.services.auth_service import generate_session_token, hash_token
        from datetime import datetime, timedelta, timezone

        users = UserRepository(db_conn)
        sessions = SessionRepository(db_conn)
        email = f"noregress-{uuid.uuid4().hex[:8]}@glintstone.example"
        user = users.create_user(email=email)
        users.link_auth_method(user["id"], "magic_link", email)
        db_conn.commit()

        raw = generate_session_token()
        token_hash = hash_token(raw)
        sessions.create_session(
            user["id"], token_hash, datetime.now(timezone.utc) + timedelta(days=1)
        )
        db_conn.commit()

        found = sessions.find_by_token_hash(token_hash)
        assert found is not None
        assert found["email"] == email

        with db_conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user["id"],))
        db_conn.commit()
