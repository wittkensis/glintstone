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
