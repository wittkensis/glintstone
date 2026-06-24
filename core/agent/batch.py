"""Batch agent-cache CLI.

Usage:
    python -m core.agent.batch summarize [OPTIONS]
    python -m core.agent.batch interpret [OPTIONS]

`summarize` seeds the artifact-summary cache. `interpret` (#411) seeds the
token-interpretation cache so the first `interpret_token` on a token is a warm
``agent_outputs`` hit (~ms) instead of the cold 30-45s Claude chain-assembly —
the UX risk on the newly-unlocked 264k surfaceless lines (#407).

summarize options:
    --limit N           Max artifacts to process (default: 100)
    --focus FOCUS       Summary focus (default: general)
    --lang LANG         Filter by language substring, e.g. "Sumerian"
    --period PERIOD     Filter by period substring, e.g. "Old Babylonian"
    --skip-cached       Skip artifacts that already have a fresh cached summary
                        (default: True — pass --no-skip-cached to force re-run)
    --dry-run           Print what would run without calling the API

interpret options:
    --limit N           Max tokens to process (default: 100)
    --surfaceless-only  Only warm tokens on surface-less lines (the #407 risk
                        surface) — default True; pass --no-surfaceless-only to
                        warm any lemmatized token.
    --skip-cached       Skip tokens that already have a fresh cached
                        interpretation (default: True)
    --dry-run           Print what would run without calling the API
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

import psycopg
from psycopg.rows import DictRow

from core.config import get_settings
from core.database import connect_one_shot

logger = logging.getLogger(__name__)

_PROMPT_VERSION = "synthesis.v2"
_INTERPRET_PROMPT_VERSION = "interpret-token.v1"
_DEFAULT_LIMIT = 100
_DEFAULT_FOCUS = "general"


def _fetch_candidates(
    conn: psycopg.Connection[DictRow],
    *,
    limit: int,
    focus: str,
    lang_filter: str | None,
    period_filter: str | None,
    skip_cached: bool,
) -> list[str]:
    """Return p_numbers eligible for summarization."""
    conditions = ["a.p_number IS NOT NULL"]
    params: list = []

    if lang_filter:
        conditions.append("a.language_normalized ILIKE %s")
        params.append(f"%{lang_filter}%")

    if period_filter:
        conditions.append("a.period ILIKE %s")
        params.append(f"%{period_filter}%")

    if skip_cached:
        conditions.append(
            """
            NOT EXISTS (
                SELECT 1 FROM agent_outputs ao
                WHERE ao.output_type = 'artifact_summary'
                  AND ao.target_type = 'artifact'
                  AND ao.target_id = a.p_number
                  AND COALESCE(ao.focus, '') = %s
                  AND ao.prompt_version = %s
                  AND ao.superseded_at IS NULL
                  AND ao.generated_at > now() - INTERVAL '30 days'
            )
            """
        )
        params.extend([focus, _PROMPT_VERSION])

    where = " AND ".join(conditions)
    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT a.p_number
            FROM artifacts a
            WHERE {where}
            ORDER BY a.p_number
            LIMIT %s
            """,
            params,
        )
        return [row["p_number"] for row in cur.fetchall()]


def cmd_summarize(args: argparse.Namespace) -> int:
    # Import here to avoid circular imports at module load time
    from api.services import agent_service  # noqa: PLC0415

    settings = get_settings()
    conn = connect_one_shot()

    candidates = _fetch_candidates(
        conn,
        limit=args.limit,
        focus=args.focus,
        lang_filter=args.lang,
        period_filter=args.period,
        skip_cached=args.skip_cached,
    )

    if not candidates:
        print("No candidates found — nothing to do.")
        return 0

    print(f"Batch summarize: {len(candidates)} artifacts, focus={args.focus}")
    if args.dry_run:
        for p in candidates:
            print(f"  [dry-run] {p}")
        return 0

    # Validate API key
    anthropic_key = (
        settings.anthropic_api_key if hasattr(settings, "anthropic_api_key") else None
    )
    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        return 1

    ok = skipped = errors = 0

    for i, p_number in enumerate(candidates, 1):
        print(f"  [{i}/{len(candidates)}] {p_number} … ", end="", flush=True)
        try:
            resp = agent_service.do_summarize_artifact(
                conn,
                p_number=p_number,
                focus=args.focus,
                interaction_id_int=None,
                interaction_id_str=f"batch-{p_number}",
            )
            if resp.data and resp.data.synthesis:
                print("ok")
                ok += 1
            else:
                print("skipped (no synthesis)")
                skipped += 1
        except Exception as exc:
            # Roll back the aborted transaction so the next artifact starts clean.
            try:
                conn.rollback()
            except Exception:
                pass
            print(f"error: {exc}")
            errors += 1

        # Small back-off to avoid hammering the Anthropic API
        if i < len(candidates):
            time.sleep(0.25)

    print(f"\nDone: {ok} ok, {skipped} skipped, {errors} errors")
    conn.close()
    return 0 if errors == 0 else 1


def _fetch_interpret_candidates(
    conn: psycopg.Connection[DictRow],
    *,
    limit: int,
    surfaceless_only: bool,
    skip_cached: bool,
) -> list[tuple[str, int]]:
    """Return (p_number, token_id) pairs eligible for interpret-cache warming.

    Only LEMMATIZED tokens are warmed — those produce a real grounded chain (an
    un-lemmatized token returns a fast hypotheses response, not the expensive
    chain). When ``surfaceless_only`` is set we restrict to tokens on surface-less
    lines (``text_lines.surface_id IS NULL``) — the newly-unlocked #407 surface
    that the issue (#411) flags as the cold-latency risk. ``skip_cached`` excludes
    tokens that already have a fresh, non-superseded cached interpretation, so the
    pass is idempotent and re-runnable.
    """
    conditions = ["lz.token_id IS NOT NULL"]
    params: list = []

    if surfaceless_only:
        conditions.append("tl.surface_id IS NULL")

    if skip_cached:
        conditions.append(
            """
            NOT EXISTS (
                SELECT 1 FROM agent_outputs ao
                WHERE ao.output_type = 'token_interpretation'
                  AND ao.target_type = 'token'
                  AND ao.target_id = t.id::text
                  AND ao.focus IS NULL
                  AND ao.prompt_version = %s
                  AND ao.superseded_at IS NULL
                  AND ao.generated_at > now() - INTERVAL '30 days'
            )
            """
        )
        params.append(_INTERPRET_PROMPT_VERSION)

    where = " AND ".join(conditions)
    params.append(limit)

    with conn.cursor() as cur:
        # DISTINCT on token id — a token can carry multiple lemmatizations, but we
        # only need to warm each token once. Ordered by p_number, token id for a
        # stable, resumable scan.
        cur.execute(
            f"""
            SELECT DISTINCT tl.p_number AS p_number, t.id AS token_id
            FROM tokens t
            JOIN text_lines tl ON t.line_id = tl.id
            JOIN lemmatizations lz ON lz.token_id = t.id
            WHERE {where}
            ORDER BY tl.p_number, t.id
            LIMIT %s
            """,
            params,
        )
        return [(row["p_number"], row["token_id"]) for row in cur.fetchall()]


def cmd_interpret(args: argparse.Namespace) -> int:
    """Warm the token-interpretation cache (#411).

    Pre-runs ``do_interpret_token`` for lemmatized tokens so the first user
    interpret is a warm cache hit (~ms) rather than the cold 30-45s chain. Same
    lazy-persist path as a live request, so it writes the SAME ``agent_outputs``
    rows a user would have triggered — no parallel cache, no schema change."""
    from api.services import agent_service  # noqa: PLC0415

    settings = get_settings()
    conn = connect_one_shot()

    candidates = _fetch_interpret_candidates(
        conn,
        limit=args.limit,
        surfaceless_only=args.surfaceless_only,
        skip_cached=args.skip_cached,
    )

    if not candidates:
        print("No candidates found — nothing to do.")
        return 0

    scope = "surface-less" if args.surfaceless_only else "all-lemmatized"
    print(f"Batch interpret: {len(candidates)} tokens, scope={scope}")
    if args.dry_run:
        for p, tid in candidates:
            print(f"  [dry-run] {p} token={tid}")
        return 0

    anthropic_key = (
        settings.anthropic_api_key if hasattr(settings, "anthropic_api_key") else None
    )
    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        return 1

    ok = skipped = errors = 0

    for i, (p_number, token_id) in enumerate(candidates, 1):
        print(
            f"  [{i}/{len(candidates)}] {p_number} token={token_id} … ",
            end="",
            flush=True,
        )
        try:
            resp = agent_service.do_interpret_token(
                conn,
                p_number=p_number,
                token_id=token_id,
                interaction_id_int=None,
                interaction_id_str=f"batch-{p_number}-{token_id}",
            )
            # do_interpret_token commits the lazy-persist insert on its own; a
            # populated chain means the cache row is now warm.
            if resp.data and (resp.data.steps or resp.data.hypotheses):
                print("ok")
                ok += 1
            else:
                print("skipped (no chain)")
                skipped += 1
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            print(f"error: {exc}")
            errors += 1

        if i < len(candidates):
            time.sleep(0.25)

    print(f"\nDone: {ok} ok, {skipped} skipped, {errors} errors")
    conn.close()
    return 0 if errors == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m core.agent.batch",
        description="Batch agent operations",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize_p = subparsers.add_parser(
        "summarize", help="Generate and cache artifact summaries"
    )
    summarize_p.add_argument("--limit", type=int, default=_DEFAULT_LIMIT)
    summarize_p.add_argument("--focus", default=_DEFAULT_FOCUS)
    summarize_p.add_argument("--lang", default=None, help="Language filter substring")
    summarize_p.add_argument("--period", default=None, help="Period filter substring")
    summarize_p.add_argument(
        "--skip-cached", action=argparse.BooleanOptionalAction, default=True
    )
    summarize_p.add_argument("--dry-run", action="store_true")

    interpret_p = subparsers.add_parser(
        "interpret", help="Warm the token-interpretation cache (#411)"
    )
    interpret_p.add_argument("--limit", type=int, default=_DEFAULT_LIMIT)
    interpret_p.add_argument(
        "--surfaceless-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Only warm tokens on surface-less lines (the #407 risk surface)",
    )
    interpret_p.add_argument(
        "--skip-cached", action=argparse.BooleanOptionalAction, default=True
    )
    interpret_p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    if args.command == "summarize":
        return cmd_summarize(args)
    if args.command == "interpret":
        return cmd_interpret(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
