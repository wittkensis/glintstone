#!/usr/bin/env python3
"""
Step 18: Import normalization bridge data into lexical schema.

Imports norms and norm-forms from ORACC glossaries into:
  - lexical_norms (normalized forms linked to lemmas)
  - lexical_norm_forms (written/orthographic spellings per norm)

Then backfills lemmatizations.norm_id FK from existing TEXT norm values.

Source data: ORACC glossary entry.norms[] arrays, each with nested forms[].
  entry (lemma) -> norms[] (normalized forms) -> forms[] (written spellings)

Projects: epsd2, dcclt, blms, etcsri, dccmt, hbtin, ribo, rinap, saao

Usage:
    python 18_import_norms.py [--dry-run] [--project PROJECT] [--skip-backfill]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

ORACC_BASE = Path(__file__).resolve().parents[1] / "sources/ORACC"

# All projects with glossaries (including epsd2)
ALL_PROJECTS = [
    "epsd2",
    "dcclt",
    "blms",
    "etcsri",
    "dccmt",
    "hbtin",
    "ribo",
    "rinap",
    "saao",
]


def find_glossary_files(project: str) -> list[Path]:
    """Find all gloss-*.json files for a project."""
    base = ORACC_BASE / project / "json" / project
    if not base.exists():
        return []
    return sorted(base.glob("gloss-*.json"))


def extract_language_code(filename: str) -> str:
    """Extract base language code from glossary filename.

    gloss-akk-x-stdbab.json -> akk
    gloss-sux.json -> sux
    """
    base = filename.replace("gloss-", "").replace(".json", "")
    if "-x-" in base:
        return base.split("-x-")[0]
    return base


def extract_full_language(filename: str) -> str:
    """Extract full language code including dialect.

    gloss-akk-x-stdbab.json -> akk-x-stdbab
    gloss-sux.json -> sux
    """
    return filename.replace("gloss-", "").replace(".json", "")


def build_lemma_cache(conn: psycopg.Connection) -> dict:
    """Build a lookup cache: (cf, gw, pos, language_code, source) -> lemma_id.

    Uses cf_gw_pos generated column + source for uniqueness.
    """
    cache = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, citation_form, guide_word, pos, language_code, source "
            "FROM lexical_lemmas"
        )
        for row in cur:
            key = (
                row["citation_form"],
                row["guide_word"],
                row["pos"],
                row["language_code"],
                row["source"],
            )
            cache[key] = row["id"]
    return cache


def import_norms_from_glossary(
    conn: psycopg.Connection,
    path: Path,
    project: str,
    lemma_cache: dict,
    dry_run: bool,
) -> dict:
    """Import norms and norm-forms from one glossary file."""
    stats = {
        "norms": 0,
        "norm_forms": 0,
        "skipped_no_lemma": 0,
        "skipped_no_norms": 0,
    }

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ! Skipping malformed file {path.name}: {e}")
        return stats

    entries = data.get("entries", [])
    if not entries:
        return stats

    language_code = extract_language_code(path.name)
    source = f"oracc/{project}" if project != "epsd2" else "epsd2"

    norms_batch = []
    norm_forms_pending = []  # (norm_key, form_data) pairs to insert after norms

    for entry in entries:
        cf = entry.get("cf")
        gw = entry.get("gw")
        pos = entry.get("pos")
        norms_data = entry.get("norms", [])

        if not norms_data:
            stats["skipped_no_norms"] += 1
            continue

        if not cf:
            stats["skipped_no_lemma"] += 1
            continue

        # Resolve lemma_id via cache
        lemma_id = lemma_cache.get((cf, gw, pos, language_code, source))
        if not lemma_id:
            stats["skipped_no_lemma"] += 1
            continue

        for norm_entry in norms_data:
            norm_text = norm_entry.get("n")
            if not norm_text:
                continue

            norm_icount = int(norm_entry.get("icount", 0))
            norm_ipct = int(norm_entry.get("ipct", 0))
            norm_source_id = norm_entry.get("id")

            norm_rec = {
                "norm": norm_text,
                "lemma_id": lemma_id,
                "attestation_count": norm_icount,
                "attestation_pct": norm_ipct,
                "source": source,
                "source_id": norm_source_id,
            }
            norms_batch.append(norm_rec)
            stats["norms"] += 1

            # Collect forms for this norm (will insert after norms are in DB)
            for form_entry in norm_entry.get("forms", []):
                form_text = form_entry.get("n")
                if not form_text:
                    continue
                form_icount = int(form_entry.get("icount", 0))
                norm_forms_pending.append(
                    {
                        "norm_key": (norm_text, lemma_id, source),
                        "written_form": form_text,
                        "attestation_count": form_icount,
                        "source": source,
                    }
                )
                stats["norm_forms"] += 1

    if dry_run:
        return stats

    # Insert norms
    if norms_batch:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO lexical_norms (
                    norm, lemma_id, attestation_count, attestation_pct,
                    source, source_id
                ) VALUES (
                    %(norm)s, %(lemma_id)s, %(attestation_count)s, %(attestation_pct)s,
                    %(source)s, %(source_id)s
                )
                ON CONFLICT (norm, lemma_id, source) DO NOTHING
                """,
                norms_batch,
            )

    # Build norm_id lookup for form insertion
    if norm_forms_pending:
        norm_id_cache = {}
        unique_norm_keys = {nf["norm_key"] for nf in norm_forms_pending}

        with conn.cursor() as cur:
            for norm_text, lemma_id, src in unique_norm_keys:
                cur.execute(
                    "SELECT id FROM lexical_norms "
                    "WHERE norm = %s AND lemma_id = %s AND source = %s",
                    (norm_text, lemma_id, src),
                )
                row = cur.fetchone()
                if row:
                    norm_id_cache[(norm_text, lemma_id, src)] = row["id"]

        # Insert norm-forms
        forms_batch = []
        for nf in norm_forms_pending:
            norm_id = norm_id_cache.get(nf["norm_key"])
            if norm_id:
                forms_batch.append(
                    {
                        "norm_id": norm_id,
                        "written_form": nf["written_form"],
                        "attestation_count": nf["attestation_count"],
                        "source": nf["source"],
                    }
                )

        if forms_batch:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO lexical_norm_forms (
                        norm_id, written_form, attestation_count, source
                    ) VALUES (
                        %(norm_id)s, %(written_form)s, %(attestation_count)s, %(source)s
                    )
                    ON CONFLICT (norm_id, written_form, source) DO NOTHING
                    """,
                    forms_batch,
                )

    conn.commit()
    return stats


def backfill_lemmatizations_norm_id(conn: psycopg.Connection, dry_run: bool) -> int:
    """Backfill lemmatizations.norm_id from existing TEXT norm values.

    Matches (norm, citation_form, guide_word, language) to lexical_norms
    via the lemma -> norm chain.
    """
    print("\n" + "=" * 80)
    print("BACKFILL: lemmatizations.norm_id")
    print("=" * 80)

    if dry_run:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM lemmatizations "
                "WHERE norm IS NOT NULL AND norm != '' AND norm_id IS NULL"
            )
            count = cur.fetchone()["cnt"]
        print(f"[DRY RUN] Would attempt to backfill {count:,} rows")
        return 0

    # Match lemmatizations.norm to lexical_norms via the parent lemma
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE lemmatizations l
            SET norm_id = ln.id
            FROM lexical_norms ln
            JOIN lexical_lemmas ll ON ln.lemma_id = ll.id
            WHERE l.norm IS NOT NULL
              AND l.norm != ''
              AND l.norm_id IS NULL
              AND l.norm = ln.norm
              AND l.citation_form = ll.citation_form
              AND l.guide_word = ll.guide_word
              AND l.language LIKE ll.language_code || '%'
        """)
        updated = cur.rowcount

    conn.commit()
    print(f"  Backfilled {updated:,} lemmatizations with norm_id")

    # Report remaining unmatched
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) as cnt FROM lemmatizations "
            "WHERE norm IS NOT NULL AND norm != '' AND norm_id IS NULL"
        )
        remaining = cur.fetchone()["cnt"]

    if remaining > 0:
        print(f"  {remaining:,} lemmatizations with norm still unmatched")

    return updated


def update_pipeline_linguistic(
    conn: psycopg.Connection, dry_run: bool
) -> tuple[int, int]:
    """Update pipeline_status.linguistic_complete for tablets with lemmatization or norm data.

    Pass 1: Tablets with full CDL lemmatizations (citation_form populated) -> 1.0
    Pass 2: Tablets with norm_id links only (normalization bridge) -> 0.5
    Order matters — Pass 1 first so tablets with both get 1.0, not 0.5.
    """
    print("\n" + "=" * 80)
    print("PIPELINE STATUS: linguistic_complete")
    print("=" * 80)

    if dry_run:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM pipeline_status ps
                WHERE (linguistic_complete IS NULL OR linguistic_complete = 0)
                AND EXISTS (
                    SELECT 1 FROM lemmatizations l
                    JOIN tokens t ON l.token_id = t.id
                    JOIN text_lines tl ON t.line_id = tl.id
                    WHERE tl.p_number = ps.p_number
                    AND l.citation_form IS NOT NULL AND l.citation_form != ''
                )
            """)
            full = cur.fetchone()["cnt"]
            cur.execute("""
                SELECT COUNT(*) as cnt FROM pipeline_status ps
                WHERE (linguistic_complete IS NULL OR linguistic_complete = 0)
                AND EXISTS (
                    SELECT 1 FROM lemmatizations l
                    JOIN tokens t ON l.token_id = t.id
                    JOIN text_lines tl ON t.line_id = tl.id
                    WHERE tl.p_number = ps.p_number AND l.norm_id IS NOT NULL
                )
            """)
            partial = cur.fetchone()["cnt"]
        print(
            f"[DRY RUN] Would set {full:,} tablets -> 1.0, up to {partial:,} tablets -> 0.5"
        )
        return 0, 0

    with conn.cursor() as cur:
        # Pass 1: Full lemmatizations -> 1.0
        cur.execute("""
            UPDATE pipeline_status ps
            SET linguistic_complete = 1.0
            WHERE (linguistic_complete IS NULL OR linguistic_complete = 0)
            AND EXISTS (
                SELECT 1 FROM lemmatizations l
                JOIN tokens t ON l.token_id = t.id
                JOIN text_lines tl ON t.line_id = tl.id
                WHERE tl.p_number = ps.p_number
                AND l.citation_form IS NOT NULL AND l.citation_form != ''
            )
        """)
        full_count = cur.rowcount

        # Pass 2: Norm-bridge-only -> 0.5
        cur.execute("""
            UPDATE pipeline_status ps
            SET linguistic_complete = 0.5
            WHERE (linguistic_complete IS NULL OR linguistic_complete = 0)
            AND EXISTS (
                SELECT 1 FROM lemmatizations l
                JOIN tokens t ON l.token_id = t.id
                JOIN text_lines tl ON t.line_id = tl.id
                WHERE tl.p_number = ps.p_number AND l.norm_id IS NOT NULL
            )
        """)
        partial_count = cur.rowcount

    conn.commit()
    print(f"  Full lemmatizations (-> 1.0): {full_count:,} tablets")
    print(f"  Norm-bridge only (-> 0.5):    {partial_count:,} tablets")

    return full_count, partial_count


def main(args):
    settings = get_settings()

    conn = psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}",
        row_factory=psycopg.rows.dict_row,
    )

    print("\n" + "=" * 80)
    print("NORMALIZATION BRIDGE IMPORT")
    print("written_form -> normalized_form -> lemma -> glosses")
    print("=" * 80)

    # Build lemma lookup cache
    print("\nBuilding lemma cache...")
    lemma_cache = build_lemma_cache(conn)
    print(f"  {len(lemma_cache):,} lemmas in cache")

    # Determine projects
    if args.project:
        if args.project not in ALL_PROJECTS:
            print(f"\n! Unknown project: {args.project}")
            print(f"Available: {', '.join(ALL_PROJECTS)}")
            return 1
        projects = [args.project]
    else:
        projects = ALL_PROJECTS

    # Phase 1: Import norms from glossaries
    print("\n" + "-" * 80)
    print("PHASE 1: Import glossary norms")
    print("-" * 80)

    grand_total = {"norms": 0, "norm_forms": 0, "skipped_no_lemma": 0, "files": 0}

    for project in projects:
        glossary_files = find_glossary_files(project)
        if not glossary_files:
            print(f"\n  ! No glossary files for {project}")
            continue

        print(f"\n  {project.upper()} ({len(glossary_files)} files)")

        for gf in glossary_files:
            stats = import_norms_from_glossary(
                conn, gf, project, lemma_cache, args.dry_run
            )

            grand_total["norms"] += stats["norms"]
            grand_total["norm_forms"] += stats["norm_forms"]
            grand_total["skipped_no_lemma"] += stats["skipped_no_lemma"]
            grand_total["files"] += 1

            if stats["norms"] > 0 or stats["norm_forms"] > 0:
                print(
                    f"    {gf.name:40} "
                    f"{stats['norms']:>6,} norms  {stats['norm_forms']:>6,} forms"
                    + (
                        f"  ({stats['skipped_no_lemma']} unmatched)"
                        if stats["skipped_no_lemma"] > 0
                        else ""
                    )
                )

    # Phase 1 summary
    print("\n" + "-" * 80)
    print("PHASE 1 TOTALS")
    print("-" * 80)
    print(f"  Files processed:    {grand_total['files']:,}")
    print(f"  Norms imported:     {grand_total['norms']:,}")
    print(f"  Norm-forms imported: {grand_total['norm_forms']:,}")
    print(f"  Skipped (no lemma): {grand_total['skipped_no_lemma']:,}")

    # Phase 2: Backfill lemmatizations.norm_id
    if not args.skip_backfill:
        backfill_lemmatizations_norm_id(conn, args.dry_run)
    else:
        print("\n  Skipping backfill (--skip-backfill)")

    # Phase 3: Update pipeline_status.linguistic_complete
    update_pipeline_linguistic(conn, args.dry_run)

    # Verification
    if not args.dry_run:
        print("\n" + "=" * 80)
        print("DATABASE VERIFICATION")
        print("=" * 80)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM lexical_norms")
            norm_count = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) as cnt FROM lexical_norm_forms")
            form_count = cur.fetchone()["cnt"]

            cur.execute(
                "SELECT COUNT(*) as cnt FROM lemmatizations WHERE norm_id IS NOT NULL"
            )
            backfill_count = cur.fetchone()["cnt"]

            # Per-source breakdown
            cur.execute(
                "SELECT source, COUNT(*) as cnt FROM lexical_norms "
                "GROUP BY source ORDER BY cnt DESC"
            )
            by_source = cur.fetchall()

        print(f"\n  lexical_norms:      {norm_count:,}")
        print(f"  lexical_norm_forms: {form_count:,}")
        print(f"  lemmatizations.norm_id backfilled: {backfill_count:,}")

        print("\n  By source:")
        for row in by_source:
            print(f"    {row['source']:20} {row['cnt']:>8,}")

    print("\n" + "=" * 80)
    print("NORMALIZATION BRIDGE IMPORT COMPLETE")
    print("=" * 80 + "\n")

    conn.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import normalization bridge data from ORACC glossaries"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without writing to database",
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Import only a specific project (e.g., dcclt, epsd2)",
    )
    parser.add_argument(
        "--skip-backfill",
        action="store_true",
        help="Skip backfilling lemmatizations.norm_id",
    )
    args = parser.parse_args()

    sys.exit(main(args))
