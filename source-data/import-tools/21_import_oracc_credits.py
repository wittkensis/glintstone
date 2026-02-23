#!/usr/bin/env python3
"""
Step 21: Import ORACC per-text credits into artifact_credits.

Reads the `credits` field from each ORACC catalogue.json and stores it
per artifact. For Q-number-keyed projects (rinap, riao, etcsri), resolves
to P-numbers via the artifact_composites table.

Sources: ORACC catalogue.json files (CC BY-SA 3.0)

Usage:
    python 21_import_oracc_credits.py [--dry-run] [--reset]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

ORACC_BASE = Path(__file__).resolve().parents[1] / "sources/ORACC"

ORACC_PROJECTS = [
    "dcclt",
    "epsd2",
    "rinap",
    "saao",
    "blms",
    "cams",
    "etcsri",
    "riao",
    "rimanum",
    "etcsl",
    "ribo",
    "rime",
    "amgg",
    "hbtin",
]

BATCH_SIZE = 1000


def load_q_to_p_map(conn: psycopg.Connection) -> dict[str, list[str]]:
    """Load Q-number → [P-numbers] mapping from artifact_composites."""
    cur = conn.execute("SELECT q_number, p_number FROM artifact_composites")
    result: dict[str, list[str]] = {}
    for q, p in cur.fetchall():
        result.setdefault(q, []).append(p)
    return result


def load_existing_p_numbers(conn: psycopg.Connection) -> set[str]:
    """Load all known P-numbers for FK validation."""
    cur = conn.execute("SELECT p_number FROM artifacts")
    return {row[0] for row in cur.fetchall()}


def find_catalogue(project: str) -> Path | None:
    """Find catalogue.json, checking multiple path patterns."""
    candidates = [
        ORACC_BASE / project / "json" / project / "catalogue.json",
        ORACC_BASE / project / "json" / "catalogue.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def main():
    parser = argparse.ArgumentParser(description="Import ORACC credits")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset", action="store_true", help="Truncate and reimport")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 21: IMPORT ORACC CREDITS")
    print("=" * 60)

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    conn = psycopg.connect(conninfo)

    if args.reset and not args.dry_run:
        print("\n  [RESET] Truncating artifact_credits...")
        conn.execute("TRUNCATE artifact_credits")
        conn.commit()

    q_to_p = load_q_to_p_map(conn)
    valid_p = load_existing_p_numbers(conn)
    print(
        f"\n  Q→P mappings: {sum(len(v) for v in q_to_p.values()):,} across {len(q_to_p):,} Q-numbers"
    )
    print(f"  Valid P-numbers: {len(valid_p):,}")

    total_inserted = 0
    total_skipped_no_fk = 0
    total_skipped_no_credits = 0

    for project in ORACC_PROJECTS:
        cat_path = find_catalogue(project)
        if not cat_path:
            continue

        try:
            with open(cat_path, encoding="utf-8") as f:
                catalogue = json.load(f)
        except (json.JSONDecodeError, ValueError):
            print(f"  {project}: invalid JSON, skipping")
            continue

        members = catalogue.get("members", {})
        batch: list[tuple[str, str, str]] = []
        proj_inserted = 0
        proj_no_fk = 0
        proj_no_credits = 0

        for text_id, entry in members.items():
            credits = entry.get("credits", "").strip()
            if not credits:
                proj_no_credits += 1
                continue

            # Resolve text_id to P-numbers
            p_numbers: list[str] = []
            if text_id.startswith("P"):
                p_numbers = [text_id]
            elif text_id.startswith("Q"):
                p_numbers = q_to_p.get(text_id, [])

            for p_number in p_numbers:
                if p_number not in valid_p:
                    proj_no_fk += 1
                    continue
                batch.append((p_number, project, credits))

            if len(batch) >= BATCH_SIZE and not args.dry_run:
                n = flush_batch(conn, batch)
                proj_inserted += n
                batch = []

        if batch and not args.dry_run:
            n = flush_batch(conn, batch)
            proj_inserted += n
        elif args.dry_run:
            proj_inserted = len(batch)

        total_inserted += proj_inserted
        total_skipped_no_fk += proj_no_fk
        total_skipped_no_credits += proj_no_credits

        if proj_inserted or proj_no_fk or proj_no_credits:
            print(
                f"  {project:12s}  inserted:{proj_inserted:>6}  no_fk:{proj_no_fk:>5}  no_credits:{proj_no_credits:>6}"
            )

    conn.close()

    print(f"\n  Total inserted: {total_inserted:,}")
    print(f"  Skipped (no FK): {total_skipped_no_fk:,}")
    print(f"  Skipped (no credits): {total_skipped_no_credits:,}")
    print("  Done.")


def flush_batch(conn: psycopg.Connection, batch: list[tuple[str, str, str]]) -> int:
    """Insert batch with ON CONFLICT skip."""
    inserted = 0
    with conn.cursor() as cur:
        for record in batch:
            cur.execute(
                """INSERT INTO artifact_credits (p_number, oracc_project, credits_text)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (p_number, oracc_project) DO NOTHING""",
                record,
            )
            inserted += cur.rowcount
    conn.commit()
    return inserted


if __name__ == "__main__":
    main()
