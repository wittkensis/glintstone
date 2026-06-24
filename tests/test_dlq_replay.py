"""Tests for Fix B (prime-suffix fallback) and the DLQ replay logic (#237/#174).

These are pure-logic tests — no database required. They exercise the shared
match helpers used by both the live connector and the replay path, and the
replay batching/marking loop against an in-memory fake connection.
"""

from __future__ import annotations

from ingestion.connectors.oracc_lemmatizations import (
    OraccLemmatizationsConnector,
    _resolve_line_ids,
    _select_line_id,
    _stash_line,
)
from ingestion import dlq_replay


# --- Fix B: prime-suffix fallback ----------------------------------------


def test_exact_match_wins():
    # cache values are (line_id, source) tuples (#254). Exact match returns the
    # whole surface map untouched.
    cache = {("P1", "2"): {"obverse": (10, "oracc")}}
    assert _resolve_line_ids(cache, "P1", "2") == {"obverse": (10, "oracc")}


def test_prime_fallback_resolves_bare_integer_to_oracc_line():
    # text_lines only has the prime variant "2'" and it is an ORACC-source line;
    # ORACC seeks "2". The fallback rescues it (#237) because the primed line is
    # itself oracc — a same-source match, so the lemma's position is valid.
    cache = {("P1", "2'"): {"obverse": (11, "oracc")}}
    assert _resolve_line_ids(cache, "P1", "2") == {"obverse": (11, "oracc")}


def test_prime_fallback_only_for_bare_integers():
    cache = {("P1", "2''"): {"obverse": (12, "oracc")}}
    # "2'" is not a bare integer, so we must NOT try "2''".
    assert _resolve_line_ids(cache, "P1", "2'") is None


def test_prime_fallback_does_not_invent_false_match():
    # No prime variant present -> stays unmatched, never a wrong line.
    cache = {("P1", "3'"): {"obverse": (13, "oracc")}}
    assert _resolve_line_ids(cache, "P1", "2") is None


def test_non_numeric_line_number_no_fallback():
    cache = {("P1", "o 2'"): {"obverse": (14, "oracc")}}
    assert _resolve_line_ids(cache, "P1", "o 2") is None


# --- #448: prime-fallback must NOT cross-match an ORACC lemma onto a CDLI line
#
# Root cause #446 found: ORACC ingests partially-preserved lines UNPRIMED
# (`1`, `5`); the CDLI ATF that also populated text_lines stores them PRIMED
# (`1'`, `5'`). The original #237 fallback returned the whole primed slot, so
# once oracc-atf (#273) made both sources coexist an ORACC lemma (unprimed `1`)
# could fall through to a CDLI primed line `1'` whose tokenisation differs —
# landing the lemma on the wrong token (126/129 of the mis-targeted positions).
# The fix scopes the prime fallback to ORACC-source primed lines only.


def test_448_prime_fallback_refuses_cdli_only_primed_line():
    # The ONLY primed variant present is a CDLI line. An ORACC lemma for line "1"
    # must NOT attach to the CDLI "1'" line (different tokenisation/section).
    # Pre-fix this returned {"reverse": (3310406, "cdli")} -> the #446 corruption.
    cache = {("P229758", "1'"): {"reverse": (3310406, "cdli")}}
    assert _resolve_line_ids(cache, "P229758", "1") is None


def test_448_prime_fallback_resolves_when_oracc_primed_line_exists():
    # A genuinely prime-mismatched ORACC line (the case #237 was meant to fix):
    # the primed slot holds an oracc-source line. The lemma's position indexes
    # ORACC tokenisation, so this same-source match is valid -> rescue it.
    cache = {("P1", "5'"): {"obverse": (2200, "oracc")}}
    assert _resolve_line_ids(cache, "P1", "5") == {"obverse": (2200, "oracc")}


def test_448_prime_fallback_filters_mixed_slot_to_oracc_only():
    # The primed slot holds BOTH a CDLI column line and the ORACC line for the
    # same physical line. The fallback must keep ONLY the oracc entry, so the
    # lemma can never resolve onto the CDLI tokenisation.
    cache = {
        ("P1", "5'"): {
            "obverse": (1500, "cdli"),
            "reverse": (2500, "oracc"),
        }
    }
    resolved = _resolve_line_ids(cache, "P1", "5")
    assert resolved == {"reverse": (2500, "oracc")}
    # and selecting from it can only yield the oracc line_id, never the cdli one
    assert _select_line_id(resolved, "reverse") == 2500


def test_448_exact_unprimed_oracc_line_never_triggers_fallback():
    # When oracc-atf has created the correct UNPRIMED oracc line, the exact match
    # wins and the (CDLI) primed line is never consulted. This is the common case
    # proven on prod for all 12 triage artifacts (1202 lemmas, 0 cdli landings).
    cache = {
        ("P229758", "1"): {"obverse": (5276577, "oracc")},
        ("P229758", "1'"): {"reverse": (3310406, "cdli")},
    }
    resolved = _resolve_line_ids(cache, "P229758", "1")
    assert resolved == {"obverse": (5276577, "oracc")}
    assert _select_line_id(resolved, "obverse") == 5276577


def test_448_genuinely_different_lines_not_cross_matched():
    # A lemma for line "7" must not borrow line "2"'s slot or any other line —
    # only its own number (exact or prime-of-7). No "7"/"7'" present -> unmatched.
    cache = {
        ("P1", "2"): {"obverse": (10, "oracc")},
        ("P1", "2'"): {"obverse": (11, "oracc")},
    }
    assert _resolve_line_ids(cache, "P1", "7") is None


def test_select_line_id_prefers_surface():
    # cache values are (line_id, source) tuples (#254); _select_line_id
    # returns just the line_id.
    line_ids = {"obverse": (1, "cdli"), "reverse": (2, "oracc")}
    assert _select_line_id(line_ids, "reverse") == 2
    # falls back to any surface when the lemma surface is absent
    assert _select_line_id({"reverse": (2, "oracc")}, "obverse") == 2
    assert _select_line_id(None, "obverse") is None


# --- #254: duplicate-line collision / oracc-source preference -------------


def test_stash_line_oracc_wins_over_cdli():
    # The same (p_number, line_number, surface) exists as a cdli column line
    # and as the oracc line. The oracc line carries the tokenization an ORACC
    # lemma's position refers to, so it must win the slot regardless of insert
    # order.
    cache: dict = {}
    _stash_line(cache, "P1", "4", "obverse", 100, "cdli")
    _stash_line(cache, "P1", "4", "obverse", 200, "oracc")
    assert _select_line_id(cache[("P1", "4")], "obverse") == 200

    # ...and the reverse insert order yields the same winner (no downgrade).
    cache2: dict = {}
    _stash_line(cache2, "P1", "4", "obverse", 200, "oracc")
    _stash_line(cache2, "P1", "4", "obverse", 100, "cdli")
    assert _select_line_id(cache2[("P1", "4")], "obverse") == 200


def test_stash_line_keeps_first_when_no_oracc():
    # No oracc line present -> keep whatever was stored first; never invent.
    cache: dict = {}
    _stash_line(cache, "P1", "4", "obverse", 100, "cdli")
    _stash_line(cache, "P1", "4", "obverse", 101, "cdli")
    assert _select_line_id(cache[("P1", "4")], "obverse") == 100


# --- #254: end-to-end build_caches + resolve against the bug fixture ------
#
# A realistic reconstruction of the prod failure (#254): a 3000-row sample of
# open `no_token_match` dead letters where ~82% had the (p,line,surface) tuple
# duplicated across sources. With blind last-writer-wins the oracc line was
# dropped and the lemma's token went unmatched. We assert the fix resolves the
# duplicated rows (the right oracc token is found at the *as-is* position — no
# -1 shift) and that the genuine residue (lemma position beyond the line's
# token count) correctly stays unresolved.


class _CacheFakeDB:
    """Serves canned text_lines + tokens rows so build_caches_for_payloads and
    resolve_payload run their real SQL-shaped logic against a fixture."""

    def __init__(self, line_rows, token_rows):
        self._line_rows = line_rows
        self._token_rows = token_rows
        self.inserts = 0

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith("SELECT id FROM annotation_runs"):
            return _FakeResult([{"id": 7}])
        if "FROM text_lines" in s:
            return _FakeResult(self._line_rows)
        if "FROM tokens" in s:
            ids = set(params[0])
            return _FakeResult([t for t in self._token_rows if t["line_id"] in ids])
        if s.startswith("INSERT INTO lemmatizations"):
            self.inserts += 1
            return _FakeResult([])
        return _FakeResult([])

    def commit(self):
        pass

    def rollback(self):
        pass


def _build_254_fixture(n_dup=82, n_residue=18):
    """Build line/token rows + dead-letter payloads modeling the #254 split.

    For each duplicated case: a cdli line (line_id 1000+i, short — only 2
    tokens, no token at the lemma position) and an oracc line (2000+i, with a
    token at the lemma position). The lemma payload targets position 2.

    For each residue case: only an oracc line exists but it has just 2 tokens
    (positions 0,1) while the lemma seeks position 2 -> genuinely unresolvable.
    """
    line_rows: list[dict] = []
    token_rows: list[dict] = []
    payloads: list[dict] = []
    tok_id = 0
    for i in range(n_dup):
        p = f"P{i:06d}"
        cdli_id, oracc_id = 1000 + i, 2000 + i
        line_rows.append(
            {
                "p_number": p,
                "line_number": "4",
                "surface_type": "obverse",
                "id": cdli_id,
                "source": "cdli",
            }
        )
        line_rows.append(
            {
                "p_number": p,
                "line_number": "4",
                "surface_type": "obverse",
                "id": oracc_id,
                "source": "oracc",
            }
        )
        # cdli line: only positions 0,1 (no pos 2)
        for pos in (0, 1):
            tok_id += 1
            token_rows.append({"id": tok_id, "line_id": cdli_id, "position": pos})
        # oracc line: positions 0,1,2 -> the lemma's token lives here
        for pos in (0, 1, 2):
            tok_id += 1
            token_rows.append({"id": tok_id, "line_id": oracc_id, "position": pos})
        payloads.append(
            {
                "project": "x",
                "p_number": p,
                "line_number": "4",
                "surface": "obverse",
                "position": 2,
                "cf": "lugal",
            }
        )
    for j in range(n_residue):
        p = f"R{j:06d}"
        oracc_id = 3000 + j
        line_rows.append(
            {
                "p_number": p,
                "line_number": "4",
                "surface_type": "obverse",
                "id": oracc_id,
                "source": "oracc",
            }
        )
        for pos in (0, 1):  # no position 2 anywhere -> genuine residue
            tok_id += 1
            token_rows.append({"id": tok_id, "line_id": oracc_id, "position": pos})
        payloads.append(
            {
                "project": "x",
                "p_number": p,
                "line_number": "4",
                "surface": "obverse",
                "position": 2,
                "cf": "lugal",
            }
        )
    return line_rows, token_rows, payloads


def test_254_oracc_preference_resolves_dup_lines_and_leaves_residue():
    line_rows, token_rows, payloads = _build_254_fixture(n_dup=82, n_residue=18)
    db = _CacheFakeDB(line_rows, token_rows)
    p_numbers = sorted({pl["p_number"] for pl in payloads})
    line_cache, token_cache = OraccLemmatizationsConnector.build_caches_for_payloads(
        db, p_numbers
    )

    resolved = 0
    for pl in payloads:
        if OraccLemmatizationsConnector.resolve_payload(
            db, pl, 7, line_cache, token_cache
        ):
            resolved += 1

    total = len(payloads)  # 100
    # ~82% resolve (the duplicated rows, via the oracc line at the as-is
    # position — proving there is NO off-by-one to compensate)...
    assert resolved == 82
    assert 0.80 <= resolved / total <= 0.85
    # ...and the ~18% genuine residue (position beyond the line) stays open.
    assert total - resolved == 18


def test_254_no_position_shift_applied():
    """Guard against a regression to the misdiagnosed `position - 1` fix: the
    token must be matched at the lemma's recorded position, not position-1."""
    line_rows = [
        {
            "p_number": "P1",
            "line_number": "4",
            "surface_type": "obverse",
            "id": 2000,
            "source": "oracc",
        },
    ]
    token_rows = [
        {"id": 1, "line_id": 2000, "position": 0},
        {"id": 2, "line_id": 2000, "position": 1},
        {"id": 3, "line_id": 2000, "position": 2},
    ]
    db = _CacheFakeDB(line_rows, token_rows)
    line_cache, token_cache = OraccLemmatizationsConnector.build_caches_for_payloads(
        db, ["P1"]
    )
    # position 2 -> token id 3 (exact). A -1 shift would wrongly pick token 2.
    assert token_cache[(2000, 2)] == 3
    payload = {
        "project": "x",
        "p_number": "P1",
        "line_number": "4",
        "surface": "obverse",
        "position": 2,
        "cf": "lugal",
    }
    assert OraccLemmatizationsConnector.resolve_payload(
        db, payload, 7, line_cache, token_cache
    )


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
