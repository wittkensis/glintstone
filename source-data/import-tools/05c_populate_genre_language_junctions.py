#!/usr/bin/env python3
"""
Step 5c: Populate genre and language junction tables.

Reads raw genre/language strings from artifacts, decomposes compound values,
and inserts normalized rows into artifact_genres / artifact_languages with
confidence scores.

Depends on:
  - Step 1 (canonical_genres, canonical_languages must be seeded)
  - Step 5 (artifacts must be imported)

Idempotent: uses ON CONFLICT DO NOTHING. Safe to re-run.

Usage:
    python 05c_populate_genre_language_junctions.py [--dry-run] [--reset]
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg

from core.config import get_settings

# Import normalization maps from seed script
from importlib import import_module

_seed = import_module("01_seed_lookup_tables")
GENRE_NORMALIZE = _seed.GENRE_NORMALIZE
LANG_NORMALIZE = _seed.LANG_NORMALIZE
LANG_SKIP = _seed.LANG_SKIP

BATCH_SIZE = 2000


def decompose_genre(raw_genre: str) -> list[dict]:
    """Split compound genre into normalized parts with confidence.

    "Administrative ?" -> [{"name": "Administrative", "conf": 0.7, "primary": True}]
    "Lexical; Mathematical" -> [
        {"name": "Lexical", "conf": 1.0, "primary": True},
        {"name": "Mathematical", "conf": 1.0, "primary": False},
    ]
    "Royal/Votive" -> [
        {"name": "Royal/Monumental", "conf": 1.0, "primary": True},
        {"name": "Votive", "conf": 1.0, "primary": False},
    ]
    """
    parts = [p.strip() for p in raw_genre.split(";") if p.strip()]
    results = []
    seen = set()

    for i, part in enumerate(parts):
        # Detect uncertainty marker
        uncertain = part.rstrip().endswith("?")
        clean = re.sub(r"\s*\?+\s*$", "", part).strip()

        # Skip uncertain/unknown genre labels
        if clean.lower() in ("uncertain", ""):
            continue

        conf = 0.7 if uncertain else 1.0

        # Look up canonical name
        canonical = GENRE_NORMALIZE.get(clean.lower())
        if not canonical:
            # Fallback: title-case
            canonical = clean.title() if clean.islower() else clean

        if canonical not in seen:
            results.append(
                {
                    "name": canonical,
                    "conf": conf,
                    "primary": len(results) == 0,
                }
            )
            seen.add(canonical)

        # Special: "Royal/Votive" should also add Votive
        if clean.lower() == "royal/votive" and "Votive" not in seen:
            results.append(
                {
                    "name": "Votive",
                    "conf": conf,
                    "primary": False,
                }
            )
            seen.add("Votive")

    return results


def decompose_language(raw_lang: str) -> list[dict]:
    """Split compound language into atomic parts with confidence.

    "Sumerian; Akkadian" -> [{"name": "Sumerian", "conf": 1.0}, {"name": "Akkadian", "conf": 1.0}]
    "Sumerian ?" -> [{"name": "Sumerian", "conf": 0.7}]
    "Akkadian; Persian; Elamite Egyptian" -> fixes missing separator
    """
    # Normalize separators: commas to semicolons
    normalized = raw_lang.replace(",", ";")
    # Fix known bad data: "Elamite Egyptian" missing separator
    normalized = normalized.replace("Elamite Egyptian", "Elamite; Egyptian")

    parts = [p.strip().rstrip(",") for p in normalized.split(";") if p.strip()]
    results = []
    seen = set()

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Detect uncertainty
        uncertain = part.rstrip().endswith("?")
        clean = re.sub(r"\s*\?+\s*$", "", part).strip()

        # Detect pseudo marker
        is_pseudo = "(pseudo)" in clean.lower()
        clean = re.sub(r"\s*\(pseudo\)", "", clean, flags=re.IGNORECASE).strip()

        # Check if this is a skip value
        if clean.lower() in LANG_SKIP:
            continue

        # Set confidence
        if is_pseudo:
            conf = 0.5
        elif uncertain:
            conf = 0.7
        else:
            conf = 1.0

        # Map to canonical name
        canonical = LANG_NORMALIZE.get(clean)
        if not canonical:
            # Try title case
            canonical = LANG_NORMALIZE.get(clean.title())
        if not canonical:
            # Unrecognized — skip with warning (printed at end)
            continue

        if canonical not in seen:
            results.append(
                {
                    "name": canonical,
                    "conf": conf,
                    "primary": len(results) == 0,
                }
            )
            seen.add(canonical)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Populate genre/language junction tables"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, no DB writes"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate junction tables before populating",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 5c: POPULATE GENRE/LANGUAGE JUNCTIONS")
    print("=" * 60)

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )

    if args.dry_run:
        print("\n[DRY RUN] No database writes.\n")

    conn = psycopg.connect(conninfo)

    if args.reset and not args.dry_run:
        print("  [RESET] Truncating junction tables...")
        conn.execute("TRUNCATE artifact_genres, artifact_languages")
        conn.commit()
        print("  Truncated.\n")

    # Load canonical ID lookups
    genre_ids: dict[str, int] = {}
    for row in conn.execute("SELECT id, name FROM canonical_genres").fetchall():
        genre_ids[row[1]] = row[0]
    print(f"  Loaded {len(genre_ids)} canonical genres")

    lang_ids: dict[str, int] = {}
    for row in conn.execute("SELECT id, name FROM canonical_languages").fetchall():
        lang_ids[row[1]] = row[0]
    print(f"  Loaded {len(lang_ids)} canonical languages")

    if not genre_ids or not lang_ids:
        print("\nERROR: canonical tables empty. Run 01_seed_lookup_tables.py first.")
        conn.close()
        sys.exit(1)

    # Process artifacts in batches
    total_artifacts = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
    print(f"  Total artifacts: {total_artifacts:,}\n")

    genre_inserted = 0
    genre_skipped = 0
    lang_inserted = 0
    lang_skipped = 0
    genre_unmapped = set()
    lang_unmapped = set()

    cursor = conn.execute(
        "SELECT p_number, genre, language FROM artifacts ORDER BY p_number"
    )

    genre_batch: list[tuple] = []
    lang_batch: list[tuple] = []
    processed = 0

    for row in cursor:
        p_number, raw_genre, raw_language = row[0], row[1], row[2]
        processed += 1

        # Decompose genre
        if raw_genre:
            parts = decompose_genre(raw_genre)
            for part in parts:
                gid = genre_ids.get(part["name"])
                if gid is None:
                    genre_unmapped.add(part["name"])
                    continue
                genre_batch.append((p_number, gid, part["conf"], part["primary"]))

        # Decompose language
        if raw_language:
            parts = decompose_language(raw_language)
            for part in parts:
                lid = lang_ids.get(part["name"])
                if lid is None:
                    lang_unmapped.add(part["name"])
                    continue
                lang_batch.append((p_number, lid, part["conf"], part["primary"]))

        # Flush genre batch
        if len(genre_batch) >= BATCH_SIZE:
            if not args.dry_run:
                with conn.cursor() as cur:
                    for rec in genre_batch:
                        try:
                            cur.execute(
                                """INSERT INTO artifact_genres
                                   (p_number, genre_id, confidence, is_primary)
                                   VALUES (%s, %s, %s, %s)
                                   ON CONFLICT DO NOTHING""",
                                rec,
                            )
                            genre_inserted += 1
                        except Exception:
                            genre_skipped += 1
                conn.commit()
            else:
                genre_inserted += len(genre_batch)
            genre_batch = []

        # Flush language batch
        if len(lang_batch) >= BATCH_SIZE:
            if not args.dry_run:
                with conn.cursor() as cur:
                    for rec in lang_batch:
                        try:
                            cur.execute(
                                """INSERT INTO artifact_languages
                                   (p_number, language_id, confidence, is_primary)
                                   VALUES (%s, %s, %s, %s)
                                   ON CONFLICT DO NOTHING""",
                                rec,
                            )
                            lang_inserted += 1
                        except Exception:
                            lang_skipped += 1
                conn.commit()
            else:
                lang_inserted += len(lang_batch)
            lang_batch = []

        if processed % 50000 == 0:
            print(
                f"  {processed:>7,} / {total_artifacts:,}  |  "
                f"genres: {genre_inserted:,}  |  langs: {lang_inserted:,}",
                end="\r",
            )

    # Final flush
    if genre_batch and not args.dry_run:
        with conn.cursor() as cur:
            for rec in genre_batch:
                try:
                    cur.execute(
                        """INSERT INTO artifact_genres
                           (p_number, genre_id, confidence, is_primary)
                           VALUES (%s, %s, %s, %s)
                           ON CONFLICT DO NOTHING""",
                        rec,
                    )
                    genre_inserted += 1
                except Exception:
                    genre_skipped += 1
        conn.commit()
    elif genre_batch:
        genre_inserted += len(genre_batch)

    if lang_batch and not args.dry_run:
        with conn.cursor() as cur:
            for rec in lang_batch:
                try:
                    cur.execute(
                        """INSERT INTO artifact_languages
                           (p_number, language_id, confidence, is_primary)
                           VALUES (%s, %s, %s, %s)
                           ON CONFLICT DO NOTHING""",
                        rec,
                    )
                    lang_inserted += 1
                except Exception:
                    lang_skipped += 1
        conn.commit()
    elif lang_batch:
        lang_inserted += len(lang_batch)

    conn.close()

    print(f"\n\n  Processed:       {processed:,}")
    print(f"  Genre rows:      {genre_inserted:,} inserted, {genre_skipped:,} skipped")
    print(f"  Language rows:   {lang_inserted:,} inserted, {lang_skipped:,} skipped")

    if genre_unmapped:
        print(f"\n  Unmapped genres ({len(genre_unmapped)}):")
        for g in sorted(genre_unmapped):
            print(f"    - {g}")

    if lang_unmapped:
        print(f"\n  Unmapped languages ({len(lang_unmapped)}):")
        for lang in sorted(lang_unmapped):
            print(f"    - {lang}")

    print("\nDone.")


if __name__ == "__main__":
    main()
