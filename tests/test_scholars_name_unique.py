"""Regression tests for #1644 — `scholars.name` must be UNIQUE.

`ingestion/connectors/scholars.py` loads through
`upsert_batch(table="scholars", unique_key=["name"])`, which renders
`INSERT INTO scholars (name) VALUES (%s) ON CONFLICT (name) DO NOTHING`.

Postgres resolves an ON CONFLICT inference clause at PLAN time, so without a
unique index on `name` that statement raises

    there is no unique or exclusion constraint matching the ON CONFLICT
    specification

on the FIRST execution — not merely when two names collide. Migration 063 adds
`scholars_name_key UNIQUE (name)`.

The schema test below is the important one: migration 024 was *recorded* as
applied while its `scholars_name_key` never existed, so "the migration is in
`_migrations`" is not evidence the constraint is there. Assert against the
catalog instead.
"""

from __future__ import annotations

import unicodedata

import pytest

from ingestion.base import ConflictPolicy, LoadStats
from ingestion.connectors.scholars import ScholarsConnector, _normalize_name
from ingestion.loader import upsert_batch

TEST_NAME = "ZZ Test Scholar (#1644)"


# ── Unit: the connector's contract with the database ───────────────────────


class _RecordingCursor:
    def __init__(self, sink: list[str]) -> None:
        self._sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._sink.append(sql)

    def fetchone(self):
        return {"inserted": True}


class _RecordingDB:
    """Minimal stand-in for the psycopg connection upsert_batch expects."""

    def __init__(self) -> None:
        self.statements: list[str] = []
        self.commits = 0

    def cursor(self):
        return _RecordingCursor(self.statements)

    def commit(self):
        self.commits += 1


class _Ctx:
    """Only `.db` is touched by ScholarsConnector.load()."""

    def __init__(self, db) -> None:
        self.db = db


def test_scholars_connector_emits_on_conflict_name():
    """Pins the contract migration 063 exists to satisfy.

    If someone changes the connector's dedup key, this test fails and the
    migration must change with it.
    """
    db = _RecordingDB()
    stats = ScholarsConnector().load(ctx=_Ctx(db), rows=[{"name": TEST_NAME}])

    assert isinstance(stats, LoadStats)
    assert len(db.statements) == 1
    sql = db.statements[0]
    assert "INSERT INTO scholars (name)" in sql
    assert "ON CONFLICT (name) DO NOTHING" in sql


def test_connector_normalizes_names_to_nfc():
    """The unique index compares bytes, so the connector must emit NFC.

    Migration 063 NFC-normalizes the stored rows for the same reason: a
    decomposed row plus a composed insert would otherwise never conflict, and
    the unique index would silently fail to dedupe anything.
    """
    decomposed = unicodedata.normalize("NFD", "Rocío Da Riva")
    assert decomposed != "Rocío Da Riva"  # sanity: the input really is NFD
    assert _normalize_name(decomposed) == unicodedata.normalize("NFC", "Rocío Da Riva")


# ── Integration: the constraint, and the collision it enables ──────────────


@pytest.fixture
def db(has_database_url):
    from core.database import connect_one_shot

    conn = connect_one_shot()
    try:
        yield conn
    finally:
        conn.close()


def test_scholars_name_has_a_unique_index(db):
    """The guard against another 024-style silent drift.

    Checks pg_index directly rather than trusting `public._migrations`.
    """
    row = db.execute(
        """
        SELECT count(*) AS n
        FROM pg_index i
        JOIN pg_attribute a
          ON a.attrelid = i.indrelid AND a.attnum = i.indkey[0]
        WHERE i.indrelid = 'public.scholars'::regclass
          AND i.indisunique
          AND i.indnkeyatts = 1
          AND a.attname = 'name'
        """
    ).fetchone()
    n = row["n"] if isinstance(row, dict) else row[0]
    assert n == 1, (
        "scholars.name has no unique index — ON CONFLICT (name) in "
        "ingestion/connectors/scholars.py will raise. Apply migration 063."
    )


def test_upsert_batch_same_name_twice_dedupes_instead_of_raising(db):
    """The exact bug from #1644, end to end.

    Before migration 063 the FIRST call raises; after it, the second call is a
    no-op skip and exactly one row exists.
    """
    db.execute("DELETE FROM scholars WHERE name = %s", (TEST_NAME,))
    db.commit()
    try:
        first = upsert_batch(
            db=db,
            table="scholars",
            rows=[{"name": TEST_NAME}],
            unique_key=["name"],
            policy=ConflictPolicy.SKIP,
        )
        assert first.inserted == 1
        assert first.skipped == 0

        second = upsert_batch(
            db=db,
            table="scholars",
            rows=[{"name": TEST_NAME}],
            unique_key=["name"],
            policy=ConflictPolicy.SKIP,
        )
        assert second.inserted == 0
        assert second.skipped == 1

        row = db.execute(
            "SELECT count(*) AS n FROM scholars WHERE name = %s", (TEST_NAME,)
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        assert n == 1
    finally:
        db.execute("DELETE FROM scholars WHERE name = %s", (TEST_NAME,))
        db.commit()


def test_no_exact_duplicate_scholar_names_remain(db):
    """Migration 063 merged the pre-existing duplicates; none should return."""
    row = db.execute(
        "SELECT count(*) AS n FROM "
        "(SELECT name FROM scholars GROUP BY name HAVING count(*) > 1) d"
    ).fetchone()
    n = row["n"] if isinstance(row, dict) else row[0]
    assert n == 0
