#!/usr/bin/env python3
"""
Step 16: Import ORACC glossaries into unified lexical schema.

Imports glossaries from all ORACC projects into:
  - lexical_lemmas (citation forms with morphological metadata)
  - lexical_senses (meanings and contextual usage)

Projects: dcclt, blms, etcsri, dccmt, hbtin, ribo, rinap, saao

Languages: Sumerian, Akkadian (all dialects), Elamite, Hurrian, Hittite, Ugaritic

Features:
  - Multi-language support (sux, akk, elx, xhu, hit, uga, etc.)
  - Dialect tracking (emesal, oldbab, stdbab, etc.)
  - Source attribution (oracc/{project})
  - Deduplication via composite key (cf_gw_pos, source)
  - Bulk inserts for performance

Usage:
    python 16_import_oracc_glossaries.py [--dry-run] [--project PROJECT]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

ORACC_BASE = Path(__file__).resolve().parents[1] / "sources/ORACC"

# All ORACC projects with glossaries (excluding epsd2 - already imported in step 15)
ORACC_PROJECTS = ["dcclt", "blms", "etcsri", "dccmt", "hbtin", "ribo", "rinap", "saao"]

# Source citations
PROJECT_CITATIONS = {
    "dcclt": "Digital Corpus of Cuneiform Lexical Texts (ORACC)",
    "blms": "Babylonian Literary and Magical Sources (ORACC)",
    "etcsri": "Electronic Text Corpus of Sumerian Royal Inscriptions (ORACC)",
    "dccmt": "Digital Corpus of Cuneiform Mathematical Texts (ORACC)",
    "hbtin": "Heritage Babylonia Tablets in Nisaba (ORACC)",
    "ribo": "Research Institute for the Study of Babylonian Oracles (ORACC)",
    "rinap": "Royal Inscriptions of the Neo-Assyrian Period (ORACC)",
    "saao": "State Archives of Assyria Online (ORACC)",
}


def find_glossary_files(project: str) -> list[Path]:
    """Find all gloss-*.json files for a project."""
    base = ORACC_BASE / project / "json" / project
    if not base.exists():
        return []
    return sorted(base.glob("gloss-*.json"))


def extract_language_code(filename: str) -> str:
    """
    Extract language code from glossary filename.

    Examples:
      gloss-sux.json → sux
      gloss-akk.json → akk
      gloss-akk-x-stdbab.json → akk
      gloss-elx.json → elx
    """
    # Remove gloss- prefix and .json suffix
    base = filename.replace("gloss-", "").replace(".json", "")

    # Extract main language code (before -x- or end)
    if "-x-" in base:
        return base.split("-x-")[0]
    return base


def extract_dialect(filename: str) -> str | None:
    """
    Extract dialect from glossary filename.

    Examples:
      gloss-akk-x-stdbab.json → stdbab
      gloss-sux-x-emesal.json → emesal
      gloss-akk.json → None
    """
    if "-x-" not in filename:
        return None

    # Extract dialect (after -x-)
    base = filename.replace("gloss-", "").replace(".json", "")
    return base.split("-x-", 1)[1]


def import_glossary_file(
    conn: psycopg.Connection,
    path: Path,
    project: str,
    dry_run: bool,
) -> dict:
    """Import one glossary file into lexical_lemmas and lexical_senses."""
    stats = {"lemmas": 0, "senses": 0, "skipped": 0}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠ Skipping malformed file {path.name}: {e}")
        return stats

    entries = data.get("entries", [])
    if not entries:
        return stats

    language_code = extract_language_code(path.name)
    dialect = extract_dialect(path.name)
    source = f"oracc/{project}"
    source_citation = PROJECT_CITATIONS.get(project, f"ORACC {project}")
    source_url = f"http://oracc.org/{project}"

    lemmas = []
    senses = []

    for entry in entries:
        # Extract core lemma data
        cf = entry.get("cf")
        gw = entry.get("gw")
        pos = entry.get("pos")

        if not cf:
            stats["skipped"] += 1
            continue

        # Build lemma record
        lemma = {
            "citation_form": cf,
            "guide_word": gw,
            "pos": pos,
            "language_code": language_code,
            "base_form": entry.get("base"),
            "dialect": dialect,
            "period": None,  # ORACC doesn't provide period in glossary
            "region": None,  # ORACC doesn't provide region in glossary
            "cognates": None,  # Could extract from cross-references
            "derived_from": None,  # Could extract from etymology
            "attestation_count": entry.get("icount", 0),  # Instance count
            "tablet_count": 0,  # Will be computed later
            "source": source,
            "source_citation": source_citation,
            "source_url": source_url,
        }
        lemmas.append(lemma)
        stats["lemmas"] += 1

        # Extract senses
        senses_data = entry.get("senses", [])
        if senses_data:
            for sense_num, sense_data in enumerate(senses_data, 1):
                # Extract definition/meaning
                mng = sense_data.get("mng") or sense_data.get("sense") or ""

                sense = {
                    "lemma_cf": cf,  # Temporary - will resolve to lemma_id
                    "sense_number": sense_num,
                    "definition_parts": [mng] if mng else [],
                    "usage_notes": sense_data.get("note"),
                    "semantic_domain": None,  # Not in ORACC glossaries
                    "typical_context": None,
                    "example_passages": [],
                    "translations": json.dumps({"en": [mng]})
                    if mng
                    else json.dumps({}),
                    "context_distribution": None,
                    "source": source,
                    "source_citation": source_citation,
                    "source_url": source_url,
                }
                senses.append(sense)
                stats["senses"] += 1

    if dry_run:
        return stats

    # Insert lemmas
    if lemmas:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO lexical_lemmas (
                    citation_form, guide_word, pos, language_code,
                    base_form, dialect, period, region,
                    cognates, derived_from,
                    attestation_count, tablet_count,
                    source, source_citation, source_url
                ) VALUES (
                    %(citation_form)s, %(guide_word)s, %(pos)s, %(language_code)s,
                    %(base_form)s, %(dialect)s, %(period)s, %(region)s,
                    %(cognates)s, %(derived_from)s,
                    %(attestation_count)s, %(tablet_count)s,
                    %(source)s, %(source_citation)s, %(source_url)s
                )
                ON CONFLICT (cf_gw_pos, source) DO NOTHING
                """,
                lemmas,
            )

    # Resolve lemma IDs for senses
    lemma_id_map = {}
    for sense in senses:
        cf = sense["lemma_cf"]
        if cf not in lemma_id_map:
            result = conn.execute(
                """
                SELECT id FROM lexical_lemmas
                WHERE citation_form = %s
                  AND language_code = %s
                  AND source = %s
                LIMIT 1
                """,
                (cf, language_code, source),
            ).fetchone()

            if result:
                lemma_id_map[cf] = result["id"]

        if cf in lemma_id_map:
            sense["lemma_id"] = lemma_id_map[cf]
            del sense["lemma_cf"]

    # Insert senses
    senses_to_insert = [s for s in senses if "lemma_id" in s]
    if senses_to_insert:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO lexical_senses (
                    lemma_id, sense_number, definition_parts, usage_notes,
                    semantic_domain, typical_context, example_passages,
                    translations, context_distribution,
                    source, source_citation, source_url
                ) VALUES (
                    %(lemma_id)s, %(sense_number)s, %(definition_parts)s, %(usage_notes)s,
                    %(semantic_domain)s, %(typical_context)s, %(example_passages)s,
                    %(translations)s::jsonb, %(context_distribution)s,
                    %(source)s, %(source_citation)s, %(source_url)s
                )
                """,
                senses_to_insert,
            )

    conn.commit()
    return stats


def import_project(
    conn: psycopg.Connection,
    project: str,
    dry_run: bool,
) -> dict:
    """Import all glossaries for one ORACC project."""
    print(f"\n{'─' * 80}")
    print(f"PROJECT: {project.upper()}")
    print(f"{'─' * 80}\n")

    glossary_files = find_glossary_files(project)

    if not glossary_files:
        print(f"⚠ No glossary files found for {project}\n")
        return {"lemmas": 0, "senses": 0, "skipped": 0, "files": 0}

    print(f"Found {len(glossary_files)} glossary files:")
    for gf in glossary_files:
        lang = extract_language_code(gf.name)
        dialect = extract_dialect(gf.name)
        if dialect:
            print(f"  • {gf.name} ({lang}, dialect: {dialect})")
        else:
            print(f"  • {gf.name} ({lang})")
    print()

    total_stats = {"lemmas": 0, "senses": 0, "skipped": 0, "files": 0}

    for glossary_file in glossary_files:
        print(f"Importing {glossary_file.name}...")

        stats = import_glossary_file(conn, glossary_file, project, dry_run)

        total_stats["lemmas"] += stats["lemmas"]
        total_stats["senses"] += stats["senses"]
        total_stats["skipped"] += stats["skipped"]
        total_stats["files"] += 1

        if not dry_run:
            print(f"  ✓ {stats['lemmas']:,} lemmas, {stats['senses']:,} senses")
        else:
            print(
                f"  [DRY RUN] Would import {stats['lemmas']:,} lemmas, {stats['senses']:,} senses"
            )

        if stats["skipped"] > 0:
            print(f"  ⚠ Skipped {stats['skipped']} entries")

    print()
    print("Project totals:")
    print(f"  Lemmas: {total_stats['lemmas']:,}")
    print(f"  Senses: {total_stats['senses']:,}")
    print(f"  Files: {total_stats['files']}")

    return total_stats


def main(args):
    settings = get_settings()

    conn = psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}",
        row_factory=psycopg.rows.dict_row,
    )

    print("\n" + "=" * 80)
    print("ORACC GLOSSARIES IMPORT (Unified Lexical Schema)")
    print("=" * 80)

    # Determine which projects to import
    if args.project:
        if args.project not in ORACC_PROJECTS:
            print(f"\n✗ Unknown project: {args.project}")
            print(f"Available projects: {', '.join(ORACC_PROJECTS)}")
            return 1
        projects = [args.project]
    else:
        projects = ORACC_PROJECTS

    # Import each project
    grand_total = {"lemmas": 0, "senses": 0, "skipped": 0, "files": 0}

    for project in projects:
        stats = import_project(conn, project, args.dry_run)
        grand_total["lemmas"] += stats["lemmas"]
        grand_total["senses"] += stats["senses"]
        grand_total["skipped"] += stats["skipped"]
        grand_total["files"] += stats["files"]

    # Print grand totals
    print("\n" + "=" * 80)
    print("GRAND TOTALS")
    print("=" * 80)
    print()
    print(f"Projects processed: {len(projects)}")
    print(f"Glossary files: {grand_total['files']}")
    print(f"Lemmas imported: {grand_total['lemmas']:,}")
    print(f"Senses imported: {grand_total['senses']:,}")

    if grand_total["skipped"] > 0:
        print(f"Entries skipped: {grand_total['skipped']:,}")

    # Verify database counts
    if not args.dry_run:
        print()
        print("=" * 80)
        print("DATABASE VERIFICATION")
        print("=" * 80)
        print()

        with conn.cursor() as cur:
            for project in projects:
                source = f"oracc/{project}"
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM lexical_lemmas WHERE source = %s",
                    (source,),
                )
                lemma_count = cur.fetchone()["cnt"]

                cur.execute(
                    "SELECT COUNT(*) as cnt FROM lexical_senses WHERE source = %s",
                    (source,),
                )
                sense_count = cur.fetchone()["cnt"]

                print(
                    f"{project:12} - Lemmas: {lemma_count:,}, Senses: {sense_count:,}"
                )

            # Total across all ORACC projects
            cur.execute(
                "SELECT COUNT(*) as cnt FROM lexical_lemmas WHERE source LIKE 'oracc/%'"
            )
            total_lemmas = cur.fetchone()["cnt"]

            cur.execute(
                "SELECT COUNT(*) as cnt FROM lexical_senses WHERE source LIKE 'oracc/%'"
            )
            total_senses = cur.fetchone()["cnt"]

        print()
        print(f"{'TOTAL':12} - Lemmas: {total_lemmas:,}, Senses: {total_senses:,}")

    print()
    print("=" * 80)
    print("✓ ORACC GLOSSARIES IMPORT COMPLETE")
    print("=" * 80)
    print()

    conn.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import ORACC glossaries into unified lexical schema"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without writing to database",
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Import only a specific project (e.g., dcclt)",
    )
    args = parser.parse_args()

    sys.exit(main(args))
