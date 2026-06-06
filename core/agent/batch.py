"""Batch summarization CLI.

Usage:
    python -m core.agent.batch summarize [OPTIONS]

Options:
    --limit N           Max artifacts to process (default: 100)
    --focus FOCUS       Summary focus (default: general)
    --lang LANG         Filter by language substring, e.g. "Sumerian"
    --period PERIOD     Filter by period substring, e.g. "Old Babylonian"
    --skip-cached       Skip artifacts that already have a fresh cached summary
                        (default: True — pass --no-skip-cached to force re-run)
    --dry-run           Print what would run without calling the API
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

import psycopg

from core.config import get_settings
from core.database import connect_one_shot

logger = logging.getLogger(__name__)

_PROMPT_VERSION = "synthesis.v2"
_DEFAULT_LIMIT = 100
_DEFAULT_FOCUS = "general"


def _fetch_candidates(
    conn: psycopg.Connection,
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
            # SAVEPOINT per artifact: a failed artifact rolls back to the savepoint
            # without aborting the entire connection (psycopg rollback trap prevention).
            conn.execute("SAVEPOINT sp_artifact")
            resp = agent_service.do_summarize_artifact(
                conn,
                p_number=p_number,
                focus=args.focus,
                interaction_id_int=None,
                interaction_id_str=f"batch-{p_number}",
            )
            conn.execute("RELEASE SAVEPOINT sp_artifact")
            if resp.data and resp.data.synthesis:
                print("ok")
                ok += 1
            else:
                print("skipped (no synthesis)")
                skipped += 1
        except Exception as exc:
            conn.execute("ROLLBACK TO SAVEPOINT sp_artifact")
            conn.execute("RELEASE SAVEPOINT sp_artifact")
            print(f"error: {exc}")
            errors += 1

        # Small back-off to avoid hammering the Anthropic API
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

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    if args.command == "summarize":
        return cmd_summarize(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
