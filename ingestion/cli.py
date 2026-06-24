"""glintstone-ingest CLI — one entry point for the framework.

Commands:
    glintstone-ingest list                    # show all registered connectors
    glintstone-ingest run <id>                # run one connector
    glintstone-ingest run-all                 # run every connector in dep order
    glintstone-ingest status [<id>]           # show recent runs (optionally filtered)
    glintstone-ingest dead-letters <id>       # show open dead letters for a connector
    glintstone-ingest dlq-replay <id>         # replay open dead letters through current logic
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from core.config import get_settings
from core.database import connect_one_shot
from ingestion.base import RunMode
from ingestion.dlq_replay import REPLAY_HANDLERS, replay
from ingestion.registry import ConnectorRegistry
from ingestion.runner import run_connector


def _registry() -> ConnectorRegistry:
    return ConnectorRegistry()


def cmd_list(args) -> int:
    reg = _registry()
    ordered = reg.ordered()
    if not ordered:
        print("No connectors registered. Add modules under ingestion/connectors/.")
        return 0
    print(f"{len(ordered)} connector(s) registered (in dependency order):\n")
    for cls in ordered:
        deps = ", ".join(cls.runs_after) or "—"
        print(f"  {cls.id:30s} {cls.kind:11s} runs_after: {deps}")
        if cls.description:
            print(f"  {'':30s} {cls.description}")
    return 0


def cmd_run(args) -> int:
    reg = _registry()
    if args.connector_id not in reg:
        print(f"Unknown connector: {args.connector_id}", file=sys.stderr)
        print(f"Known: {[c.id for c in reg.all()]}", file=sys.stderr)
        return 1
    cls = reg.get(args.connector_id)
    settings = get_settings()
    mode = RunMode(args.mode) if args.mode else RunMode.FULL

    # Build the connector config. `argv` is always carried for provenance (it is
    # recorded in import_runs.config_json). On top of that, a scoped run can pass
    # connector-readable keys two ways, merged in this order (later wins):
    #   --config '<JSON object>'   arbitrary keys, e.g. {"projects":[...],"limit":5}
    #   --project P1 --project P2  shorthand that becomes {"projects":[...]}
    # Connectors read these via ctx.config.get("projects") etc. (e.g. oracc-atf).
    config: dict = {"argv": sys.argv[1:]}
    if args.config:
        try:
            parsed = json.loads(args.config)
        except json.JSONDecodeError as exc:
            print(f"--config is not valid JSON: {exc}", file=sys.stderr)
            return 2
        if not isinstance(parsed, dict):
            print(
                "--config must be a JSON object (e.g. '{\"projects\":[...]}')",
                file=sys.stderr,
            )
            return 2
        config.update(parsed)
    if args.project:
        # --project is additive shorthand; it does not clobber a "projects" list
        # already supplied via --config, it extends it.
        existing = config.get("projects") or []
        if not isinstance(existing, list):
            existing = [existing]
        config["projects"] = existing + list(args.project)

    summary = run_connector(
        cls,
        mode=mode,
        app_env=settings.app_env,
        force=args.force,
        config=config,
    )
    print()
    print(f"Run {summary['run_id']} — {summary['status']}")
    for k in ("inserted", "updated", "skipped", "dead_lettered"):
        if k in summary:
            print(f"  {k:15s} {summary[k]:,}")
    return 0 if summary.get("status") in ("succeeded", "no_op") else 1


def cmd_run_all(args) -> int:
    reg = _registry()
    settings = get_settings()
    mode = RunMode(args.mode) if args.mode else RunMode.FULL
    failed = 0
    for cls in reg.ordered():
        print(f"\n=== {cls.id} ===")
        try:
            summary = run_connector(
                cls,
                mode=mode,
                app_env=settings.app_env,
                force=args.force,
            )
            print(f"  → {summary['status']}")
            if summary.get("status") == "failed":
                failed += 1
                if not args.continue_on_failure:
                    print("Stopping (use --continue-on-failure to keep going).")
                    return 1
        except Exception as exc:
            failed += 1
            print(f"  → failed: {exc}")
            if not args.continue_on_failure:
                return 1
    return 0 if failed == 0 else 1


def cmd_status(args) -> int:
    db = connect_one_shot()
    try:
        if args.connector_id:
            rows = db.execute(
                """
                SELECT id, connector_id, run_mode, app_env, started_at, finished_at,
                       status, rows_inserted, rows_updated, rows_skipped,
                       rows_dead_lettered, duration_ms
                FROM import_runs
                WHERE connector_id = %s
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (args.connector_id, args.limit),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT * FROM v_ingestion_status
                ORDER BY last_run_at DESC NULLS LAST
                """,
            ).fetchall()
        if not rows:
            print("No runs recorded yet.")
            return 0
        for row in rows:
            print(dict(row))
        return 0
    finally:
        db.close()


def cmd_dead_letters(args) -> int:
    db = connect_one_shot()
    try:
        rows = db.execute(
            """
            SELECT id, run_id, category, subcategory, source_key, reason,
                   resolution_status, created_at
            FROM import_dead_letters
            WHERE connector_id = %s AND resolution_status = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (args.connector_id, args.status, args.limit),
        ).fetchall()
        if not rows:
            print(f"No '{args.status}' dead letters for {args.connector_id}.")
            return 0
        print(f"{len(rows)} '{args.status}' dead letter(s) for {args.connector_id}:\n")
        for r in rows:
            r = dict(r)
            print(
                f"  #{r['id']}  [{r['category']}/{r['subcategory'] or '—'}]  "
                f"{r['source_key'] or ''}"
            )
            print(f"    reason: {r['reason']}")
        return 0
    finally:
        db.close()


def cmd_dlq_replay(args) -> int:
    if args.connector_id not in REPLAY_HANDLERS:
        print(
            f"No DLQ replay handler for {args.connector_id}. "
            f"Known: {sorted(REPLAY_HANDLERS)}",
            file=sys.stderr,
        )
        return 1
    db = connect_one_shot()
    try:

        def _progress(p: dict) -> None:
            print(
                f"  ... examined {p['examined']:,}  "
                f"{'would-fix' if args.dry_run else 'fixed'} {p['fixed']:,}",
                flush=True,
            )

        before = _open_count(db, args.connector_id, args.category, args.subcategory)
        summary = replay(
            db,
            args.connector_id,
            category=args.category,
            subcategory=args.subcategory,
            limit=args.limit,
            dry_run=args.dry_run,
            progress=_progress,
        )
        after = _open_count(db, args.connector_id, args.category, args.subcategory)
        mode = "DRY-RUN" if args.dry_run else "REPLAY"
        print()
        print(f"{mode} — {args.connector_id}")
        print(f"  examined          {summary['examined']:,}")
        label = "would resolve" if args.dry_run else "resolved (fixed)"
        print(f"  {label:17s} {summary['fixed']:,}")
        print(f"  still open        {summary['still_open']:,}")
        print(f"  open before       {before:,}")
        print(f"  open after        {after:,}")
        return 0
    finally:
        db.close()


def _open_count(db, connector_id, category, subcategory) -> int:
    clauses = ["connector_id = %s", "resolution_status = 'open'"]
    params: list = [connector_id]
    if category:
        clauses.append("category = %s")
        params.append(category)
    if subcategory:
        clauses.append("subcategory = %s")
        params.append(subcategory)
    row = db.execute(
        f"SELECT COUNT(*) AS n FROM import_dead_letters WHERE {' AND '.join(clauses)}",
        tuple(params),
    ).fetchone()
    return row["n"] if isinstance(row, dict) else row[0]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="glintstone-ingest")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="show registered connectors")

    p_run = sub.add_parser("run", help="run one connector")
    p_run.add_argument("connector_id")
    p_run.add_argument(
        "--mode",
        choices=[m.value for m in RunMode],
        default=RunMode.FULL.value,
    )
    p_run.add_argument(
        "--force",
        action="store_true",
        help="run even if source checksum matches last successful run",
    )
    p_run.add_argument(
        "--config",
        default=None,
        metavar="JSON",
        help=(
            "JSON object of connector config for a scoped run, e.g. "
            '--config \'{"projects":["rinap","saao"]}\'. Keys are read by '
            "the connector via ctx.config (projects, limit, orcids, ...)."
        ),
    )
    p_run.add_argument(
        "--project",
        action="append",
        default=None,
        metavar="SLUG",
        help=(
            "Shorthand for a subset run: repeatable, becomes "
            "config['projects']. e.g. --project rinap --project saao"
        ),
    )

    p_all = sub.add_parser("run-all", help="run every connector in dep order")
    p_all.add_argument(
        "--mode", choices=[m.value for m in RunMode], default=RunMode.FULL.value
    )
    p_all.add_argument("--force", action="store_true")
    p_all.add_argument("--continue-on-failure", action="store_true")

    p_st = sub.add_parser("status", help="show run history")
    p_st.add_argument("connector_id", nargs="?", default=None)
    p_st.add_argument("--limit", type=int, default=10)

    p_dl = sub.add_parser("dead-letters", help="show dead-letter queue")
    p_dl.add_argument("connector_id")
    p_dl.add_argument(
        "--status",
        default="open",
        choices=["open", "investigating", "wontfix", "fixed", "duplicate"],
    )
    p_dl.add_argument("--limit", type=int, default=25)

    p_rp = sub.add_parser(
        "dlq-replay",
        help="replay open dead letters through the current connector logic",
    )
    p_rp.add_argument("connector_id")
    p_rp.add_argument("--category", default=None, help="filter by dead-letter category")
    p_rp.add_argument(
        "--subcategory", default=None, help="filter by dead-letter subcategory"
    )
    p_rp.add_argument(
        "--limit",
        type=int,
        default=None,
        help="cap how many dead letters are examined (default: all open)",
    )
    p_rp.add_argument(
        "--dry-run",
        action="store_true",
        help="report counts without writing lemmatizations or marking rows fixed",
    )

    args = parser.parse_args(argv)

    handlers = {
        "list": cmd_list,
        "run": cmd_run,
        "run-all": cmd_run_all,
        "status": cmd_status,
        "dead-letters": cmd_dead_letters,
        "dlq-replay": cmd_dlq_replay,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
