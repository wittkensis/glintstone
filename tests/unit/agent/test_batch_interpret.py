"""#411 — token-interpretation cache-warm batch.

Covers the candidate-selection SQL shape, the surfaceless/skip-cached gating,
and the cmd_interpret warm loop (mocked agent_service so no Claude call).
"""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

from core.agent.batch import (
    _INTERPRET_PROMPT_VERSION,
    _fetch_interpret_candidates,
    cmd_interpret,
    main,
)


def _fake_conn(rows):
    cur = MagicMock()
    cur.fetchall.return_value = rows
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


def test_fetch_candidates_surfaceless_and_skip_cached():
    """surfaceless_only adds the surface_id IS NULL gate; skip_cached adds the
    NOT EXISTS against the token_interpretation cache with the right prompt ver."""
    conn, cur = _fake_conn([{"p_number": "P1", "token_id": 7}])
    out = _fetch_interpret_candidates(
        conn, limit=50, surfaceless_only=True, skip_cached=True
    )
    assert out == [("P1", 7)]
    sql, params = cur.execute.call_args[0]
    assert "tl.surface_id IS NULL" in sql
    assert "token_interpretation" in sql
    assert "lemmatizations lz" in sql
    assert _INTERPRET_PROMPT_VERSION in params
    assert params[-1] == 50  # LIMIT bound last


def test_fetch_candidates_no_gates_when_flags_off():
    conn, cur = _fake_conn([])
    _fetch_interpret_candidates(
        conn, limit=10, surfaceless_only=False, skip_cached=False
    )
    sql, params = cur.execute.call_args[0]
    assert "tl.surface_id IS NULL" not in sql
    assert "NOT EXISTS" not in sql
    assert params == [10]  # only LIMIT


def test_cmd_interpret_warms_each_candidate():
    """cmd_interpret calls do_interpret_token once per candidate (the warm pass)."""
    args = argparse.Namespace(
        limit=2, surfaceless_only=True, skip_cached=True, dry_run=False
    )
    chain = MagicMock()
    chain.steps = [MagicMock()]
    chain.hypotheses = None
    resp = MagicMock(data=chain)

    with (
        patch("core.agent.batch.connect_one_shot") as conn_factory,
        patch("core.agent.batch.get_settings") as settings,
        patch(
            "core.agent.batch._fetch_interpret_candidates",
            return_value=[("P1", 1), ("P2", 2)],
        ),
        patch("api.services.agent_service.do_interpret_token", return_value=resp) as di,
        patch("core.agent.batch.time.sleep"),
    ):
        settings.return_value.anthropic_api_key = "sk-test"
        conn_factory.return_value = MagicMock()
        rc = cmd_interpret(args)

    assert rc == 0
    assert di.call_count == 2


def test_cmd_interpret_dry_run_makes_no_calls():
    args = argparse.Namespace(
        limit=5, surfaceless_only=True, skip_cached=True, dry_run=True
    )
    with (
        patch("core.agent.batch.connect_one_shot", return_value=MagicMock()),
        patch("core.agent.batch.get_settings"),
        patch(
            "core.agent.batch._fetch_interpret_candidates",
            return_value=[("P1", 1)],
        ),
        patch("api.services.agent_service.do_interpret_token") as di,
    ):
        rc = cmd_interpret(args)
    assert rc == 0
    di.assert_not_called()


def test_interpret_subcommand_is_wired():
    """The `interpret` subcommand routes to cmd_interpret."""
    with patch("core.agent.batch.cmd_interpret", return_value=0) as ci:
        rc = main(["interpret", "--limit", "3"])
    assert rc == 0
    ci.assert_called_once()
    ns = ci.call_args[0][0]
    assert ns.limit == 3
    assert ns.surfaceless_only is True
