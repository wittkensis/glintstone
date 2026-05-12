"""Tests for ingestion.dead_letters.DeadLetterSink."""

from __future__ import annotations

import pytest

from ingestion.dead_letters import DeadLetterCategory, DeadLetterSink


def test_category_enum_values_match_db_constraint():
    """The DB CHECK constraint must accept every Python enum value."""
    expected = {
        "validation_failed",
        "no_match",
        "missing_reference",
        "schema_drift",
        "duplicate",
        "other",
    }
    assert {c.value for c in DeadLetterCategory} == expected


def test_write_rejects_invalid_category(has_database_url):
    from core.database import connect_one_shot

    db = connect_one_shot()
    try:
        sink = DeadLetterSink(db)
        with pytest.raises(ValueError, match="Invalid"):
            sink.write(
                run_id=1,
                connector_id="x",
                category="not_a_real_category",
                payload={},
                reason="test",
            )
    finally:
        db.close()


def test_write_and_count_and_resolve(has_database_url):
    """End-to-end: open a run, write 3 letters, count, mark fixed, count again."""
    from core.database import connect_one_shot

    db = connect_one_shot()
    try:
        # Seed source + run
        db.execute(
            """
            INSERT INTO sources (id, display_name, kind)
            VALUES ('test-connector', 'Test Connector', 'derived')
            ON CONFLICT (id) DO NOTHING
            """
        )
        run_row = db.execute(
            """
            INSERT INTO import_runs (connector_id, app_env, status)
            VALUES ('test-connector', 'test', 'running')
            RETURNING id
            """
        ).fetchone()
        run_id = run_row["id"]
        db.commit()

        sink = DeadLetterSink(db)
        ids = [
            sink.write(
                run_id=run_id,
                connector_id="test-connector",
                category=DeadLetterCategory.NO_MATCH.value,
                payload={"k": i},
                reason=f"test {i}",
            )
            for i in range(3)
        ]
        assert sink.count_open("test-connector") == 3

        # Resolve two
        n = sink.resolve(ids[:2], status="fixed", note="patched upstream")
        assert n == 2
        assert sink.count_open("test-connector") == 1

        # Cleanup
        db.execute(
            "DELETE FROM import_dead_letters WHERE connector_id = 'test-connector'"
        )
        db.execute("DELETE FROM import_runs WHERE id = %s", (run_id,))
        db.execute("DELETE FROM sources WHERE id = 'test-connector'")
        db.commit()
    finally:
        db.close()


def test_write_many_inserts_all_rows_in_one_batch(has_database_url):
    """write_many should bulk-insert N rows with one commit, preserving payload."""
    from core.database import connect_one_shot

    db = connect_one_shot()
    try:
        db.execute(
            """
            INSERT INTO sources (id, display_name, kind)
            VALUES ('test-bulk', 'Bulk Test', 'derived')
            ON CONFLICT (id) DO NOTHING
            """
        )
        run_row = db.execute(
            """
            INSERT INTO import_runs (connector_id, app_env, status)
            VALUES ('test-bulk', 'test', 'running')
            RETURNING id
            """
        ).fetchone()
        run_id = run_row["id"]
        db.commit()

        sink = DeadLetterSink(db)
        rows = [
            {
                "category": DeadLetterCategory.NO_MATCH.value,
                "subcategory": "no_line_match",
                "source_key": f"dcclt/P00{i:04d}/1/0",
                "payload": {"project": "dcclt", "i": i},
                "reason": "no matching text_line",
            }
            for i in range(250)
        ]
        n = sink.write_many(run_id=run_id, connector_id="test-bulk", rows=rows)
        assert n == 250
        assert sink.count_open("test-bulk") == 250

        # Spot-check payload round-trip
        sample = db.execute(
            "SELECT payload, subcategory FROM import_dead_letters "
            "WHERE connector_id = 'test-bulk' AND source_key = 'dcclt/P000017/1/0'"
        ).fetchone()
        assert sample["subcategory"] == "no_line_match"
        assert sample["payload"]["i"] == 17

        # Empty input is a no-op (no commit, no error)
        assert sink.write_many(run_id=run_id, connector_id="test-bulk", rows=[]) == 0

        db.execute("DELETE FROM import_dead_letters WHERE connector_id = 'test-bulk'")
        db.execute("DELETE FROM import_runs WHERE id = %s", (run_id,))
        db.execute("DELETE FROM sources WHERE id = 'test-bulk'")
        db.commit()
    finally:
        db.close()


def test_write_many_rejects_invalid_category(has_database_url):
    """One bad category in the batch should fail before any row is written."""
    from core.database import connect_one_shot

    db = connect_one_shot()
    try:
        sink = DeadLetterSink(db)
        with pytest.raises(ValueError, match="Invalid"):
            sink.write_many(
                run_id=1,
                connector_id="x",
                rows=[
                    {
                        "category": DeadLetterCategory.NO_MATCH.value,
                        "payload": {},
                        "reason": "ok",
                    },
                    {"category": "not_a_real_category", "payload": {}, "reason": "bad"},
                ],
            )
    finally:
        db.close()
