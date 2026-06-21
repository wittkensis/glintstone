"""Tests for Fix B (prime-suffix fallback) and the DLQ replay logic (#237/#174).

These are pure-logic tests — no database required. They exercise the shared
match helpers used by both the live connector and the replay path, and the
replay batching/marking loop against an in-memory fake connection.
"""

from __future__ import annotations

from ingestion.connectors.oracc_lemmatizations import (
    _resolve_line_ids,
    _select_line_id,
)
from ingestion import dlq_replay


# --- Fix B: prime-suffix fallback ----------------------------------------


def test_exact_match_wins():
    cache = {("P1", "2"): {"obverse": 10}}
    assert _resolve_line_ids(cache, "P1", "2") == {"obverse": 10}


def test_prime_fallback_resolves_bare_integer():
    # text_lines only has the prime variant "2'"; ORACC seeks "2".
    cache = {("P1", "2'"): {"obverse": 11}}
    assert _resolve_line_ids(cache, "P1", "2") == {"obverse": 11}


def test_prime_fallback_only_for_bare_integers():
    cache = {("P1", "2''"): {"obverse": 12}}
    # "2'" is not a bare integer, so we must NOT try "2''".
    assert _resolve_line_ids(cache, "P1", "2'") is None


def test_prime_fallback_does_not_invent_false_match():
    # No prime variant present -> stays unmatched, never a wrong line.
    cache = {("P1", "3'"): {"obverse": 13}}
    assert _resolve_line_ids(cache, "P1", "2") is None


def test_non_numeric_line_number_no_fallback():
    cache = {("P1", "o 2'"): {"obverse": 14}}
    assert _resolve_line_ids(cache, "P1", "o 2") is None


def test_select_line_id_prefers_surface():
    line_ids = {"obverse": 1, "reverse": 2}
    assert _select_line_id(line_ids, "reverse") == 2
    # falls back to any surface when the lemma surface is absent
    assert _select_line_id({"reverse": 2}, "obverse") == 2
    assert _select_line_id(None, "obverse") is None


# --- DLQ replay loop ------------------------------------------------------


class _FakeResult:
    def __init__(self, rows, rowcount=0):
        self._rows = rows
        self.rowcount = rowcount

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeDB:
    """Minimal stand-in: serves canned SELECT results and records UPDATEs."""

    def __init__(self):
        self.fixed_ids: list[int] = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith("UPDATE import_dead_letters"):
            ids = params[0]
            self.fixed_ids.extend(ids)
            return _FakeResult([], rowcount=len(ids))
        # any SELECT used by the handler stub returns nothing
        return _FakeResult([])

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_replay_marks_only_resolved_rows(monkeypatch):
    db = _FakeDB()

    batches = [
        [{"id": 1, "payload": {}}, {"id": 2, "payload": {}}],
        [{"id": 3, "payload": {}}],
    ]
    calls = {"i": 0}

    def fake_fetch(db_, cid, cat, sub, after_id, size):
        i = calls["i"]
        calls["i"] += 1
        return batches[i] if i < len(batches) else []

    # handler resolves id 1 and 3, leaves 2 open
    def fake_handler(db_, rows, dry_run):
        return [r["id"] for r in rows if r["id"] in (1, 3)]

    monkeypatch.setattr(dlq_replay, "_fetch_batch", fake_fetch)
    monkeypatch.setitem(
        dlq_replay.REPLAY_HANDLERS, "oracc-lemmatizations", fake_handler
    )

    summary = dlq_replay.replay(db, "oracc-lemmatizations")
    assert summary["examined"] == 3
    assert summary["fixed"] == 2
    assert summary["still_open"] == 1
    assert sorted(db.fixed_ids) == [1, 3]


def test_dry_run_writes_nothing(monkeypatch):
    db = _FakeDB()
    batches = [[{"id": 5, "payload": {}}]]
    calls = {"i": 0}

    def fake_fetch(db_, cid, cat, sub, after_id, size):
        i = calls["i"]
        calls["i"] += 1
        return batches[i] if i < len(batches) else []

    def fake_handler(db_, rows, dry_run):
        assert dry_run is True
        return [r["id"] for r in rows]

    monkeypatch.setattr(dlq_replay, "_fetch_batch", fake_fetch)
    monkeypatch.setitem(
        dlq_replay.REPLAY_HANDLERS, "oracc-lemmatizations", fake_handler
    )

    summary = dlq_replay.replay(db, "oracc-lemmatizations", dry_run=True)
    assert summary["fixed"] == 1  # projected
    assert db.fixed_ids == []  # nothing marked
