"""End-to-end tests for ingestion.runner.run_connector against Neon.

Uses a synthetic connector built in-test (no source files on disk) to verify:
- import_runs row created with correct stats
- Dead letters routed when transform yields a bad record
- Re-run with same checksum short-circuits to status='no_op'
- Failed run records status='failed' with error_summary
"""

from __future__ import annotations

from typing import Iterator

import pytest

from ingestion.base import (
    ConflictPolicy,
    LoadStats,
    RunContext,
    RunMode,
    SourceConnector,
    SourceManifest,
)
from ingestion.dead_letters import DeadLetterCategory
from ingestion.loader import upsert_batch
from ingestion.runner import run_connector


class _SyntheticConnector(SourceConnector):
    """Built only for the integration tests below. Yields 3 good + 1 bad rows."""

    id = "test-synth"
    display_name = "Synthetic Test Connector"
    kind = "catalog"
    runs_after = []
    description = "Used only by tests/test_ingestion_runner.py"

    checksum_override: str | None = "synth-v1"
    fail_at_load: bool = False

    def discover(self, ctx: RunContext) -> SourceManifest:
        return SourceManifest(checksum=self.checksum_override)

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        yield {"p_number": "PTESTS01", "designation": "row 1"}
        yield {"p_number": "PTESTS02", "designation": "row 2"}
        yield {"p_number": "", "designation": "BAD: missing key"}
        yield {"p_number": "PTESTS03", "designation": "row 3"}

    def transform(self, ctx: RunContext, record: dict) -> Iterator[dict]:
        if not record.get("p_number"):
            ctx.dead_letter(
                category=DeadLetterCategory.VALIDATION_FAILED.value,
                subcategory="missing_p_number",
                payload=record,
                reason="empty p_number",
            )
            return
        yield record

    def load(self, ctx: RunContext, rows) -> LoadStats:
        if self.fail_at_load:
            raise RuntimeError("intentional test failure")
        return upsert_batch(
            ctx.db,
            table="staging_cdli_catalog",
            rows=rows,
            unique_key=["p_number"],
            policy=ConflictPolicy.UPDATE,
        )


def _cleanup(db):
    db.execute("DELETE FROM import_dead_letters WHERE connector_id = 'test-synth'")
    db.execute(
        "DELETE FROM import_run_events WHERE run_id IN (SELECT id FROM import_runs WHERE connector_id = 'test-synth')"
    )
    db.execute("DELETE FROM import_runs WHERE connector_id = 'test-synth'")
    db.execute("DELETE FROM staging_cdli_catalog WHERE p_number LIKE 'PTESTS%'")
    db.execute("DELETE FROM sources WHERE id = 'test-synth'")
    db.commit()


@pytest.fixture
def clean_synth(has_database_url):
    from core.database import connect_one_shot

    db = connect_one_shot()
    _cleanup(db)
    yield db
    _cleanup(db)
    db.close()


def test_run_connector_records_full_run_lifecycle(clean_synth):
    summary = run_connector(
        _SyntheticConnector,
        mode=RunMode.FULL,
        app_env="test",
    )
    assert summary["status"] == "succeeded"
    assert summary["inserted"] == 3
    assert summary["dead_lettered"] == 1

    db = clean_synth
    run = db.execute(
        "SELECT * FROM import_runs WHERE id = %s", (summary["run_id"],)
    ).fetchone()
    assert run["status"] == "succeeded"
    assert run["rows_inserted"] == 3
    assert run["rows_dead_lettered"] == 1
    assert run["source_checksum"] == "synth-v1"
    assert run["duration_ms"] is not None and run["duration_ms"] >= 0

    dl = db.execute(
        "SELECT category, subcategory FROM import_dead_letters WHERE connector_id = 'test-synth'"
    ).fetchall()
    assert len(dl) == 1
    assert dl[0]["category"] == "validation_failed"
    assert dl[0]["subcategory"] == "missing_p_number"

    events = db.execute(
        "SELECT COUNT(*) AS n FROM import_run_events WHERE run_id = %s",
        (summary["run_id"],),
    ).fetchone()
    assert events["n"] > 0


def test_run_connector_short_circuits_on_unchanged_source(clean_synth):
    first = run_connector(_SyntheticConnector, mode=RunMode.FULL, app_env="test")
    assert first["status"] == "succeeded"
    second = run_connector(_SyntheticConnector, mode=RunMode.FULL, app_env="test")
    assert second["status"] == "no_op"


def test_run_connector_force_flag_overrides_short_circuit(clean_synth):
    run_connector(_SyntheticConnector, mode=RunMode.FULL, app_env="test")
    second = run_connector(
        _SyntheticConnector, mode=RunMode.FULL, app_env="test", force=True
    )
    assert second["status"] == "succeeded"


def test_run_connector_records_failure(clean_synth):
    class _Failing(_SyntheticConnector):
        id = "test-synth"
        fail_at_load = True

    with pytest.raises(RuntimeError, match="intentional"):
        run_connector(_Failing, mode=RunMode.FULL, app_env="test")

    db = clean_synth
    failed = db.execute(
        "SELECT status, error_summary FROM import_runs WHERE connector_id = 'test-synth' ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    assert failed["status"] == "failed"
    assert "intentional" in (failed["error_summary"] or "")


def test_run_connector_upserts_source_metadata(clean_synth):
    run_connector(_SyntheticConnector, mode=RunMode.FULL, app_env="test")
    db = clean_synth
    src = db.execute(
        "SELECT id, display_name, kind FROM sources WHERE id = 'test-synth'"
    ).fetchone()
    assert src is not None
    assert src["display_name"] == "Synthetic Test Connector"
    assert src["kind"] == "catalog"
