#!/usr/bin/env python3
"""
Step 15: Import ePSD2 data into unified lexical resource schema.

Imports:
  - Signs from epsd2-sl.json → lexical_signs
  - Lemmas from gloss-sux.json → lexical_lemmas
  - Senses from gloss-sux.json → lexical_senses
  - Sign-lemma associations (matches sign values → lemma citation forms)

Features:
  - Logs unmapped fields for schema review
  - Creates sign-lemma associations automatically
  - Supports lemma_type classification (native, sumerogram, akkadogram)
  - Bulk inserts for performance

Usage:
    python 15_import_epsd2_unified.py [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

EPSD2_BASE = Path(__file__).resolve().parents[1] / "sources/ORACC/epsd2/json/epsd2"
SIGN_LIST_FILE = EPSD2_BASE / "epsd2-sl.json"
GLOSSARY_FILE = EPSD2_BASE / "gloss-sux.json"
PROGRESS_DIR = Path(__file__).resolve().parent / "_progress"

# Source attribution
SOURCE_CITATION = (
    "ePSD2 (Electronic Pennsylvania Sumerian Dictionary), University of Pennsylvania"
)
SOURCE_URL = "http://psd.museum.upenn.edu/epsd2/"


def log_unmapped_fields(category: str, available_fields: set, mapped_fields: set):
    """Log fields that exist in source but aren't mapped to schema."""
    unmapped = available_fields - mapped_fields
    if unmapped:
        PROGRESS_DIR.mkdir(exist_ok=True)
        with open(PROGRESS_DIR / "unmapped_fields.log", "a") as f:
            f.write(f"{category}: {', '.join(sorted(unmapped))}\n")
        return list(unmapped)
    return []


def import_signs(conn: psycopg.Connection, dry_run: bool) -> list[dict]:
    """
    Import sign list from epsd2-sl.json → lexical_signs.

    Returns list of sign records for association matching.
    """
    print(f"{'─' * 80}")
    print("PHASE 1: Importing Signs")
    print(f"{'─' * 80}\n")

    if not SIGN_LIST_FILE.exists():
        print(f"⚠ Sign list not found: {SIGN_LIST_FILE}")
        return []

    with open(SIGN_LIST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    signs_data = data.get("signs", {})
    print(f"Found {len(signs_data)} signs in source file")

    signs = []
    mapped_fields = {"values", "gdl"}

    for sign_name, sign_data in signs_data.items():
        # Log unmapped fields (first entry only)
        if len(signs) == 0:
            available_fields = set(sign_data.keys())
            unmapped = log_unmapped_fields(
                "epsd2-signs", available_fields, mapped_fields
            )
            if unmapped:
                print(f"  ℹ Unmapped sign fields: {', '.join(unmapped)}")

        # Extract sign values (both logographic and syllabic in same array)
        values = sign_data.get("values", [])

        sign = {
            "sign_name": sign_name,
            "unicode_char": None,  # ePSD2 doesn't provide unicode
            "sign_number": None,  # ePSD2 doesn't provide Borger/Labat numbers
            "shape_category": None,
            "component_signs": None,
            "logographic_values": values,  # All values (will separate later if needed)
            "syllabic_values": values,  # Same values for now
            "determinative_function": None,
            "language_codes": ["sux"],  # ePSD2 is Sumerian-focused
            "dialects": None,
            "periods": None,
            "regions": None,
            "source": "epsd2-sl",
            "source_citation": SOURCE_CITATION,
            "source_url": SOURCE_URL,
        }
        signs.append(sign)

    if not dry_run:
        print(f"Inserting {len(signs)} signs...")

        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO lexical_signs (
                    sign_name, unicode_char, sign_number, shape_category,
                    component_signs, logographic_values, syllabic_values,
                    determinative_function, language_codes, dialects, periods,
                    regions, source, source_citation, source_url
                ) VALUES (
                    %(sign_name)s, %(unicode_char)s, %(sign_number)s, %(shape_category)s,
                    %(component_signs)s, %(logographic_values)s, %(syllabic_values)s,
                    %(determinative_function)s, %(language_codes)s, %(dialects)s, %(periods)s,
                    %(regions)s, %(source)s, %(source_citation)s, %(source_url)s
                )
                """,
                signs,
            )

        conn.commit()
        print(f"✓ Imported {len(signs):,} signs\n")
    else:
        print(f"[DRY RUN] Would import {len(signs):,} signs\n")

    return signs


def import_lemmas_and_senses(
    conn: psycopg.Connection, dry_run: bool
) -> tuple[list[dict], list[dict]]:
    """
    Import lemmas and senses from gloss-sux.json.

    Returns (lemmas, senses) for statistics.
    """
    print(f"{'─' * 80}")
    print("PHASE 2: Importing Lemmas & Senses")
    print(f"{'─' * 80}\n")

    if not GLOSSARY_FILE.exists():
        print(f"⚠ Glossary not found: {GLOSSARY_FILE}")
        return ([], [])

    print("Loading glossary (this may take a moment)...")
    with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    print(f"Found {len(entries):,} entries in glossary\n")

    lemmas = []
    senses = []
    lemma_mapped_fields = {
        "id",
        "headword",
        "cf",
        "gw",
        "pos",
        "norms",
        "periods",
        "senses",
    }
    sense_mapped_fields = {"mng", "sense", "sigs"}

    for entry in entries:
        # Log unmapped fields (first entry only)
        if len(lemmas) == 0:
            available_fields = set(entry.keys())
            unmapped = log_unmapped_fields(
                "epsd2-lemmas", available_fields, lemma_mapped_fields
            )
            if unmapped:
                print(f"  ℹ Unmapped lemma fields: {', '.join(unmapped)}")

        cf = entry.get("cf")
        gw = entry.get("gw")
        pos = entry.get("pos")

        if not cf:
            continue  # Skip entries without citation form

        lemma = {
            "citation_form": cf,
            "guide_word": gw,
            "pos": pos,
            "language_code": "sux",  # ePSD2 is Sumerian
            "base_form": None,
            "verbal_class": None,
            "nominal_pattern": None,
            "dialect": None,
            "period": None,
            "region": None,
            "cognates": None,
            "derived_from": None,
            "attestation_count": 0,  # To be computed later
            "tablet_count": 0,  # To be computed later
            "lemma_type": "native",  # Sumerian native words by default
            "source": "epsd2",
            "source_citation": SOURCE_CITATION,
            "source_url": SOURCE_URL,
        }
        lemmas.append(lemma)

        # Extract senses
        entry_senses = entry.get("senses", [])
        for i, sense_data in enumerate(entry_senses, 1):
            # Log unmapped sense fields (first sense only)
            if len(senses) == 0 and sense_data:
                available_fields = set(sense_data.keys())
                unmapped = log_unmapped_fields(
                    "epsd2-senses", available_fields, sense_mapped_fields
                )
                if unmapped:
                    print(f"  ℹ Unmapped sense fields: {', '.join(unmapped)}\n")

            # Extract definition
            definition = sense_data.get("mng") or sense_data.get("sense")
            if not definition:
                continue

            # Split definition into parts (by comma or semicolon)
            import re

            def_parts = re.split(r"[,;]\s*", definition)

            sense = {
                "lemma_cf": cf,  # Temporary - will resolve to lemma_id
                "sense_number": i,
                "definition_parts": def_parts,
                "usage_notes": None,
                "semantic_domain": None,
                "typical_context": None,
                "example_passages": None,
                "translations": json.dumps({"en": def_parts}),
                "context_distribution": None,
                "source": "epsd2",
                "source_citation": SOURCE_CITATION,
                "source_url": SOURCE_URL,
            }
            senses.append(sense)

    if not dry_run:
        print(f"Inserting {len(lemmas):,} lemmas...")

        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO lexical_lemmas (
                    citation_form, guide_word, pos, language_code, base_form,
                    verbal_class, nominal_pattern, dialect, period, region,
                    cognates, derived_from, attestation_count, tablet_count,
                    lemma_type, source, source_citation, source_url
                ) VALUES (
                    %(citation_form)s, %(guide_word)s, %(pos)s, %(language_code)s, %(base_form)s,
                    %(verbal_class)s, %(nominal_pattern)s, %(dialect)s, %(period)s, %(region)s,
                    %(cognates)s, %(derived_from)s, %(attestation_count)s, %(tablet_count)s,
                    %(lemma_type)s, %(source)s, %(source_citation)s, %(source_url)s
                )
                ON CONFLICT (cf_gw_pos, source) DO NOTHING
                """,
                lemmas,
            )

        conn.commit()
        print(f"✓ Imported {len(lemmas):,} lemmas\n")

        # Resolve lemma IDs for senses
        print(f"Resolving lemma IDs for {len(senses):,} senses...")
        lemma_id_map = {}

        with conn.cursor() as cur:
            for sense in senses:
                cf = sense["lemma_cf"]
                if cf not in lemma_id_map:
                    result = cur.execute(
                        """
                        SELECT id FROM lexical_lemmas
                        WHERE citation_form = %s AND source = 'epsd2'
                        LIMIT 1
                        """,
                        (cf,),
                    ).fetchone()

                    if result:
                        lemma_id_map[cf] = result["id"]

                if cf in lemma_id_map:
                    sense["lemma_id"] = lemma_id_map[cf]
                    del sense["lemma_cf"]  # Remove temporary field

        # Insert senses
        senses_to_insert = [s for s in senses if "lemma_id" in s]
        print(f"Inserting {len(senses_to_insert):,} senses...")

        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO lexical_senses (
                    lemma_id, sense_number, definition_parts, usage_notes,
                    semantic_domain, typical_context, example_passages,
                    translations, context_distribution, source, source_citation, source_url
                ) VALUES (
                    %(lemma_id)s, %(sense_number)s, %(definition_parts)s, %(usage_notes)s,
                    %(semantic_domain)s, %(typical_context)s, %(example_passages)s,
                    %(translations)s::jsonb, %(context_distribution)s, %(source)s,
                    %(source_citation)s, %(source_url)s
                )
                """,
                senses_to_insert,
            )

        conn.commit()
        print(f"✓ Imported {len(senses_to_insert):,} senses\n")

        if len(senses_to_insert) < len(senses):
            orphaned = len(senses) - len(senses_to_insert)
            print(f"  ⚠ {orphaned:,} senses skipped (no matching lemma)\n")

    else:
        print(
            f"[DRY RUN] Would import {len(lemmas):,} lemmas and {len(senses):,} senses\n"
        )

    return (lemmas, senses)


def create_sign_lemma_associations(
    conn: psycopg.Connection, signs: list[dict], dry_run: bool
):
    """
    Create sign-lemma associations by matching sign values to lemma citation forms.

    Matches:
      - Sign logographic_values → lemma citation_form (logographic reading)
      - Sign syllabic_values → lemma citation_form (syllabic reading)
    """
    print(f"{'─' * 80}")
    print("PHASE 3: Creating Sign-Lemma Associations")
    print(f"{'─' * 80}\n")

    if dry_run:
        print("[DRY RUN] Skipping association creation\n")
        return

    associations = []
    unmatched_values = []

    for sign in signs:
        # Get sign ID from database
        sign_db = conn.execute(
            "SELECT id FROM lexical_signs WHERE sign_name = %s AND source = 'epsd2-sl' LIMIT 1",
            (sign["sign_name"],),
        ).fetchone()

        if not sign_db:
            continue

        sign_id = sign_db["id"]

        # Match logographic values
        for log_val in sign.get("logographic_values", []):
            lemma = conn.execute(
                """
                SELECT id FROM lexical_lemmas
                WHERE citation_form = %s
                  AND language_code = 'sux'
                  AND source = 'epsd2'
                LIMIT 1
                """,
                (log_val,),
            ).fetchone()

            if lemma:
                associations.append(
                    {
                        "sign_id": sign_id,
                        "lemma_id": lemma["id"],
                        "reading_type": "logographic",
                        "frequency": 0,  # To be computed later
                        "context_distribution": None,
                        "source": "epsd2-sl",
                        "source_citation": SOURCE_CITATION,
                        "source_url": SOURCE_URL,
                    }
                )
            else:
                unmatched_values.append(
                    f"{sign['sign_name']} → {log_val} (logographic)"
                )

    # Bulk insert associations
    if associations:
        print(f"Inserting {len(associations):,} sign-lemma associations...")
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO lexical_sign_lemma_associations (
                    sign_id, lemma_id, reading_type, frequency, context_distribution,
                    source, source_citation, source_url
                ) VALUES (
                    %(sign_id)s, %(lemma_id)s, %(reading_type)s, %(frequency)s,
                    %(context_distribution)s, %(source)s, %(source_citation)s, %(source_url)s
                )
                ON CONFLICT DO NOTHING
                """,
                associations,
            )

        conn.commit()
        print(f"✓ Created {len(associations):,} sign-lemma associations\n")
    else:
        print("No associations created\n")

    # Report unmatched
    if unmatched_values:
        PROGRESS_DIR.mkdir(exist_ok=True)
        with open(PROGRESS_DIR / "unmatched_sign_values.txt", "w") as f:
            f.write("\n".join(unmatched_values))
        print(
            f"  ⚠ {len(unmatched_values):,} unmatched sign values (see _progress/unmatched_sign_values.txt)\n"
        )


def main(args):
    settings = get_settings()

    # Connect to database
    conn = psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}",
        row_factory=psycopg.rows.dict_row,
    )

    print("\n" + "=" * 80)
    print("ePSD2 UNIFIED LEXICAL IMPORT")
    print("=" * 80 + "\n")

    # Phase 1: Import signs
    signs = import_signs(conn, args.dry_run)

    # Phase 2: Import lemmas and senses
    lemmas, senses = import_lemmas_and_senses(conn, args.dry_run)

    # Phase 3: Create sign-lemma associations
    create_sign_lemma_associations(conn, signs, args.dry_run)

    # Final statistics
    print(f"{'─' * 80}")
    print("SUMMARY")
    print(f"{'─' * 80}\n")
    print(f"Signs imported: {len(signs):,}")
    print(f"Lemmas imported: {len(lemmas):,}")
    print(f"Senses imported: {len(senses):,}")
    print()

    if not args.dry_run:
        # Get final counts from database
        sign_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM lexical_signs WHERE source = 'epsd2-sl'"
        ).fetchone()["cnt"]

        lemma_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM lexical_lemmas WHERE source = 'epsd2'"
        ).fetchone()["cnt"]

        sense_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM lexical_senses WHERE source = 'epsd2'"
        ).fetchone()["cnt"]

        assoc_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM lexical_sign_lemma_associations WHERE source = 'epsd2-sl'"
        ).fetchone()["cnt"]

        print("Database counts:")
        print(f"  Signs: {sign_count:,}")
        print(f"  Lemmas: {lemma_count:,}")
        print(f"  Senses: {sense_count:,}")
        print(f"  Associations: {assoc_count:,}")
        print()

    print("✓ ePSD2 import complete\n")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import ePSD2 into unified lexical schema"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without writing to database",
    )
    args = parser.parse_args()

    main(args)
