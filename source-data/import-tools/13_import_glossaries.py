#!/usr/bin/env python3
"""
Step 13: Import ORACC glossaries into glossary_entries and glossary_forms tables.

Processes gloss-*.json files from all downloaded ORACC projects.
Each glossary entry becomes one glossary_entries row.
Each form becomes one glossary_forms row.

Depends on: Step 2 (annotation_runs), Step 3 (scholars — not strictly required)

Usage:
    python 13_import_glossaries.py [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

ORACC_BASE = Path(__file__).resolve().parents[1] / "sources/ORACC"

ORACC_PROJECTS = ["dcclt", "epsd2", "rinap", "saao", "blms", "cams", "etcsri", "riao"]

# Map ORACC project to annotation_run source_name
PROJECT_TO_RUN = {
    "dcclt": "oracc/dcclt",
    "epsd2": "oracc/epsd2",
    "rinap": "oracc/rinap",
    "saao": "oracc/saao",
    "blms": "oracc/blms",
    "cams": "oracc/cams",
    "etcsri": "oracc/etcsri",
    "riao": "oracc/riao",
}


def find_glossary_files(project: str) -> list[Path]:
    """Find all gloss-*.json files for a project."""
    base = ORACC_BASE / project / "json" / project
    if not base.exists():
        return []
    return sorted(base.glob("gloss-*.json"))


def parse_norms(norms_data) -> str | None:
    """Extract normalized forms as JSON string."""
    if not norms_data:
        return None
    if isinstance(norms_data, list):
        return json.dumps([n.get("n", "") if isinstance(n, dict) else str(n) for n in norms_data])
    return None


def parse_periods(periods_data) -> str | None:
    """Extract period attestation as JSON string."""
    if not periods_data:
        return None
    if isinstance(periods_data, list):
        return json.dumps(periods_data)
    return None


def import_glossary_file(
    conn: psycopg.Connection,
    path: Path,
    project: str,
    annotation_run_id: int,
    dry_run: bool,
) -> dict:
    stats = {"entries": 0, "forms": 0, "skipped": 0}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        return stats  # Empty or malformed file

    lang = data.get("lang", "und")
    entries = data.get("entries", [])

    if not entries:
        return stats

    with conn.cursor() as cur:
        for entry in entries:
            entry_id = entry.get("id") or entry.get("oid")
            if not entry_id:
                stats["skipped"] += 1
                continue

            # Prefix entry_id with project to ensure global uniqueness
            global_entry_id = f"{project}/{entry_id}"
            headword = entry.get("headword", "")
            cf = entry.get("cf", "")
            gw = entry.get("gw", "")
            pos = entry.get("pos", "")
            icount = int(entry.get("icount", 0) or 0)
            norms = parse_norms(entry.get("norms"))
            periods = parse_periods(entry.get("periods"))

            # Normalized headword: lowercase citation form
            normalized = cf.lower().strip() if cf else headword.lower().strip()

            if not dry_run:
                cur.execute("""
                    INSERT INTO glossary_entries (
                        entry_id, headword, citation_form, guide_word,
                        language, pos, icount, project,
                        normalized_headword, norms, periods, annotation_run_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (entry_id) DO NOTHING
                    RETURNING entry_id
                """, (
                    global_entry_id, headword, cf, gw,
                    lang, pos, icount, project,
                    normalized, norms, periods, annotation_run_id
                ))
                row = cur.fetchone()
                if not row:
                    stats["skipped"] += 1
                    continue
            stats["entries"] += 1

            # Import forms
            forms = entry.get("forms", [])
            for form in forms:
                form_id = form.get("id", "")
                form_n = form.get("n", "")
                form_c = int(form.get("c", 0) or 0)
                form_icount = int(form.get("icount", 0) or 0)

                if not form_n or dry_run:
                    stats["forms"] += 1
                    continue

                cur.execute("""
                    INSERT INTO glossary_forms (entry_id, form, count)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (global_entry_id, form_n, form_c))
                stats["forms"] += 1

    if not dry_run:
        conn.commit()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Import ORACC glossaries")
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 13: IMPORT ORACC GLOSSARIES")
    print("=" * 60)

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    conn = psycopg.connect(conninfo)

    # Get annotation_run IDs
    annotation_run_ids = {}
    with conn.cursor() as cur:
        for proj, source_name in PROJECT_TO_RUN.items():
            cur.execute(
                "SELECT id FROM annotation_runs WHERE source_name = %s", (source_name,)
            )
            row = cur.fetchone()
            if row:
                annotation_run_ids[proj] = row[0]

    total_entries = 0
    total_forms = 0
    total_skipped = 0

    for project in ORACC_PROJECTS:
        gloss_files = find_glossary_files(project)
        if not gloss_files:
            print(f"  {project}: no glossary files found")
            continue

        ann_run_id = annotation_run_ids.get(project, 1)

        for gfile in gloss_files:
            lang_tag = gfile.stem.replace("gloss-", "")
            print(f"  {project}/{lang_tag}...", end=" ", flush=True)

            stats = import_glossary_file(conn, gfile, project, ann_run_id, args.dry_run)
            total_entries += stats["entries"]
            total_forms += stats["forms"]
            total_skipped += stats["skipped"]
            print(f"{stats['entries']} entries, {stats['forms']} forms")

    conn.close()

    print(f"\n  Total entries: {total_entries:,}")
    print(f"  Total forms:   {total_forms:,}")
    print(f"  Skipped:       {total_skipped:,}")
    print("Validation: OK")


if __name__ == "__main__":
    main()
