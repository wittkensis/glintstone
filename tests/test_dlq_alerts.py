"""Unit tests for dead-letter open-count alerting (issue #175).

Covers the growth-detection logic and the three alert channels (event log,
stderr, status file) with an in-memory fake DB + ctx — no real database. The
end-to-end wiring into the runner is exercised by test_ingestion_runner.py
(skipped unless DATABASE_URL is set).
"""

from __future__ import annotations

import json
from pathlib import Path

from ingestion.dlq_alerts import check_and_alert


class _FakeCtx:
    """Minimal RunContext stand-in. `open_now` and `prev_open` drive the logic."""

    def __init__(
        self, *, open_now: int, prev_open: int | None, run_id: int = 99
    ) -> None:
        self.connector_id = "test-connector"
        self.run_id = run_id
        self._open_now = open_now
        self._prev_open = prev_open
        self.recorded_open_after: int | None = None
        self.events: list[tuple[str, str, dict]] = []
        self.db = self  # ctx.db.execute(...) routes back here

    # --- fake db ---
    def execute(self, sql: str, params=None):
        s = " ".join(sql.split()).lower()
        if "count(*)" in s and "import_dead_letters" in s:
            return _Result({"n": self._open_now})
        if "dlq_open_after" in s and "select" in s:
            if self._prev_open is None:
                return _Result(None)
            return _Result({"dlq_open_after": self._prev_open})
        if "update import_runs set dlq_open_after" in s:
            self.recorded_open_after = params[0]
            return _Result(None)
        raise AssertionError(f"unexpected SQL: {s}")

    def commit(self):
        pass

    def rollback(self):
        pass

    # --- fake ctx event channels ---
    def info(self, msg, **ctx):
        self.events.append(("info", msg, ctx))

    def error(self, msg, **ctx):
        self.events.append(("error", msg, ctx))


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


def test_growth_past_threshold_alerts(tmp_path: Path) -> None:
    ctx = _FakeCtx(open_now=10, prev_open=3)
    res = check_and_alert(ctx, threshold=0, alert_dir=tmp_path)
    assert res.alerted is True
    assert res.open_now == 10
    assert res.grew_by == 7
    # error event emitted (durable, dashboard-visible channel)
    assert any(
        lvl == "error" and msg == "dlq.open_count_grew" for lvl, msg, _ in ctx.events
    )
    # baseline recorded for next run
    assert ctx.recorded_open_after == 10
    # status file written and marked bleeding
    status = json.loads((tmp_path / "test-connector.json").read_text())
    assert status["status"] == "bleeding"
    assert status["grew_by"] == 7


def test_no_growth_does_not_alert(tmp_path: Path) -> None:
    ctx = _FakeCtx(open_now=3, prev_open=3)
    res = check_and_alert(ctx, threshold=0, alert_dir=tmp_path)
    assert res.alerted is False
    assert not any(msg == "dlq.open_count_grew" for _, msg, _ in ctx.events)
    status = json.loads((tmp_path / "test-connector.json").read_text())
    assert status["status"] == "ok"


def test_threshold_tolerates_small_growth(tmp_path: Path) -> None:
    ctx = _FakeCtx(open_now=5, prev_open=3)
    res = check_and_alert(ctx, threshold=2, alert_dir=tmp_path)
    # grew by 2, threshold 2 → not past threshold
    assert res.alerted is False


def test_first_run_baseline_is_zero(tmp_path: Path) -> None:
    # No prior run recorded → baseline 0 → any open dead letters alert.
    ctx = _FakeCtx(open_now=4, prev_open=None)
    res = check_and_alert(ctx, threshold=0, alert_dir=tmp_path)
    assert res.alerted is True
    assert res.open_before is None
    assert res.grew_by == 4


def test_first_run_clean_does_not_alert(tmp_path: Path) -> None:
    ctx = _FakeCtx(open_now=0, prev_open=None)
    res = check_and_alert(ctx, threshold=0, alert_dir=tmp_path)
    assert res.alerted is False
    assert ctx.recorded_open_after == 0
