"""Tests for ingestion.loader.upsert_batch — covers SKIP vs UPDATE policy
and identifier-safety guards."""

from __future__ import annotations

import pytest

from ingestion.base import ConflictPolicy
from ingestion.loader import upsert_batch, _safe_ident


def test_safe_ident_accepts_alnum_underscore():
    assert _safe_ident("artifacts")
    assert _safe_ident("staging_cdli_catalog")
    assert _safe_ident("p_number")


def test_safe_ident_rejects_punctuation():
    assert not _safe_ident("'; DROP TABLE x; --")
    assert not _safe_ident("table-with-dash")
    assert not _safe_ident("")
    assert not _safe_ident("table name")


def test_upsert_batch_rejects_unsafe_table_name():
    with pytest.raises(ValueError, match="Identifiers"):
        upsert_batch(
            db=None,
            table="bad; drop",
            rows=[{"x": 1}],
            unique_key=["x"],
        )


def test_upsert_batch_empty_input_returns_zero_stats():
    stats = upsert_batch(
        db=None, table="staging_cdli_catalog", rows=[], unique_key=["p_number"]
    )
    assert stats.inserted == stats.updated == stats.skipped == 0


def test_upsert_batch_integration_skip_policy(has_database_url):
    """Insert two rows, re-insert same — second pass yields skipped=2."""
    from core.database import connect_one_shot

    db = connect_one_shot()
    try:
        # Clean slate
        db.execute("DELETE FROM staging_cdli_catalog WHERE p_number LIKE 'PTEST%'")
        db.commit()

        rows = [
            {"p_number": "PTEST001", "designation": "test artifact 1"},
            {"p_number": "PTEST002", "designation": "test artifact 2"},
        ]
        s1 = upsert_batch(
            db=db,
            table="staging_cdli_catalog",
            rows=rows,
            unique_key=["p_number"],
            policy=ConflictPolicy.SKIP,
        )
        assert s1.inserted == 2
        assert s1.skipped == 0

        s2 = upsert_batch(
            db=db,
            table="staging_cdli_catalog",
            rows=rows,
            unique_key=["p_number"],
            policy=ConflictPolicy.SKIP,
        )
        assert s2.inserted == 0
        assert s2.skipped == 2

        db.execute("DELETE FROM staging_cdli_catalog WHERE p_number LIKE 'PTEST%'")
        db.commit()
    finally:
        db.close()


def test_upsert_batch_integration_update_policy(has_database_url):
    """Insert then re-insert with changed value → second pass yields updated=1."""
    from core.database import connect_one_shot

    db = connect_one_shot()
    try:
        db.execute("DELETE FROM staging_cdli_catalog WHERE p_number = 'PTESTU01'")
        db.commit()

        s1 = upsert_batch(
            db=db,
            table="staging_cdli_catalog",
            rows=[{"p_number": "PTESTU01", "designation": "first"}],
            unique_key=["p_number"],
            policy=ConflictPolicy.UPDATE,
        )
        assert s1.inserted == 1

        s2 = upsert_batch(
            db=db,
            table="staging_cdli_catalog",
            rows=[{"p_number": "PTESTU01", "designation": "second"}],
            unique_key=["p_number"],
            policy=ConflictPolicy.UPDATE,
        )
        assert s2.updated == 1
        assert s2.inserted == 0

        row = db.execute(
            "SELECT designation FROM staging_cdli_catalog WHERE p_number = 'PTESTU01'"
        ).fetchone()
        assert row["designation"] == "second"

        db.execute("DELETE FROM staging_cdli_catalog WHERE p_number = 'PTESTU01'")
        db.commit()
    finally:
        db.close()
