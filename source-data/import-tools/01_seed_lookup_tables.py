#!/usr/bin/env python3
"""
Step 1: Seed normalization lookup tables from CDLI source data.

Reads distinct values from cdli_cat.csv and populates:
  - period_canon
  - language_map
  - genre_canon
  - provenience_canon
  - surface_canon

All inserts are ON CONFLICT DO NOTHING — safe to re-run.

Usage:
    python 01_seed_lookup_tables.py [--dry-run]
"""

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg

from core.config import get_settings

CDLI_CSV = Path(__file__).resolve().parents[1] / "sources/CDLI/metadata/cdli_cat.csv"


# ─────────────────────────────────────────────────────────
# LANGUAGE MAP  (CDLI label → ORACC ISO code + family)
# ─────────────────────────────────────────────────────────
LANGUAGE_MAP = [
    # cdli_name, oracc_code, full_name, family
    ("Sumerian", "sux", "Sumerian", "sumerian"),
    ("Sumerian ?", "sux", "Sumerian (uncertain)", "sumerian"),
    ("Akkadian", "akk", "Akkadian", "semitic"),
    ("Akkadian ?", "akk", "Akkadian (uncertain)", "semitic"),
    ("Akkadian (pseudo)", "akk", "Pseudo-Akkadian", "semitic"),
    ("Akkadian, Aramaic", "akk", "Akkadian and Aramaic", "semitic"),
    ("Akkadian, Aramaic?", "akk", "Akkadian and Aramaic (uncertain)", "semitic"),
    ("Eblaite", "xeb", "Eblaite", "semitic"),
    ("Ugaritic", "uga", "Ugaritic", "semitic"),
    ("Aramaic", "arc", "Aramaic", "semitic"),
    ("Aramaic ?", "arc", "Aramaic (uncertain)", "semitic"),
    ("Hebrew", "hbo", "Hebrew", "semitic"),
    ("Hebrew ?", "hbo", "Hebrew (uncertain)", "semitic"),
    ("Phoenician", "phn", "Phoenician", "semitic"),
    ("Sabaean", "xsa", "Sabaean", "semitic"),
    ("Qatabanian", "xqt", "Qatabanian", "semitic"),
    ("Arabic", "arb", "Arabic", "semitic"),
    ("Mandaic", "mid", "Mandaic", "semitic"),
    ("Syriac", "syc", "Syriac", "semitic"),
    ("Hittite", "hit", "Hittite", "hittite"),
    ("Hittite ?", "hit", "Hittite (uncertain)", "hittite"),
    ("Luwian", "xlu", "Luwian", "hittite"),
    ("Hattic", "xht", "Hattic", "other"),
    ("Elamite", "elx", "Elamite", "elamite"),
    ("Elamite Egyptian", "elx", "Elamite/Egyptian", "elamite"),
    ("Persian", "peo", "Old Persian", "other"),
    ("Persian,", "peo", "Old Persian", "other"),
    ("Persian, Babylonian", "peo", "Old Persian and Babylonian", "other"),
    ("Persian, Elamite", "peo", "Old Persian and Elamite", "other"),
    (
        "Persian, Elamite, Babylonian",
        "peo",
        "Old Persian, Elamite, and Babylonian",
        "other",
    ),
    ("Egyptian", "egy", "Egyptian", "other"),
    ("Egyptian ?", "egy", "Egyptian (uncertain)", "other"),
    ("Greek", "grc", "Greek", "other"),
    ("Hurrian", "hur", "Hurrian", "hurrian"),
    ("Hurrian ?", "hur", "Hurrian (uncertain)", "hurrian"),
    ("Urartian", "xur", "Urartian", "other"),
    ("Sumerian, Akkadian", "sux", "Sumerian and Akkadian", "sumerian"),
    ("undetermined", "und", "Undetermined", "other"),
    ("undetermined (pseudo)", "und", "Pseudo-inscription", "other"),
    ("no linguistic content", "none", "No linguistic content", "other"),
    ("uncertain", "und", "Uncertain", "other"),
    ("unclear", "und", "Unclear", "other"),
    ("uninscribed", "none", "Uninscribed", "other"),
    ("clay", "none", "Clay (no text)", "other"),
]

# ─────────────────────────────────────────────────────────
# SURFACE CANON  (ATF markers → canonical names)
# ─────────────────────────────────────────────────────────
SURFACE_CANON = [
    ("@obverse", "obverse"),
    ("@reverse", "reverse"),
    ("@left", "left_edge"),
    ("@right", "right_edge"),
    ("@top", "top_edge"),
    ("@bottom", "bottom_edge"),
    ("@seal", "seal"),
    ("@edge", "unknown"),
    ("@face", "unknown"),
    ("@a", "obverse"),
    ("@b", "reverse"),
    ("Obv", "obverse"),
    ("Rev", "reverse"),
    ("obverse", "obverse"),
    ("reverse", "reverse"),
    ("left edge", "left_edge"),
    ("right edge", "right_edge"),
    ("top edge", "top_edge"),
    ("bottom edge", "bottom_edge"),
    ("", "unknown"),
]


def parse_period(raw: str) -> dict | None:
    """
    Parse a raw CDLI period string into canonical form + date range.

    Handles:
      "Ur III (ca. 2100-2000 BC)"      → canonical="Ur III", start=2100, end=2000
      "Ur III (ca. 2100-2000 BC) ?"    → canonical="Ur III", start=2100, end=2000
      "Neo-Babylonian (626-539 BC)"    → canonical="Neo-Babylonian"
      "Sassanian (224-641 AD)"         → canonical="Sassanian", start=-224, end=-641
      "uncertain"                       → canonical="uncertain", start=None, end=None
      "fake (modern)"                   → canonical="fake (modern)", start=None, end=None
      Multi-period (two periods joined) → skip (too ambiguous)
    """
    raw = raw.strip()
    if not raw:
        return None

    # Strip trailing "?" and whitespace
    clean = re.sub(r"\s*\?$", "", raw).strip()

    # Skip multi-period entries (contain ", " between two period names)
    # e.g. "ED I-II (ca. 2900-2700 BC), Old Babylonian (ca. 1900-1600 BC)"
    if re.search(r"\)\s*,\s*[A-Z]", clean):
        # Store as-is with NULL dates
        return {"raw": raw, "canonical": clean, "start": None, "end": None}

    # Pattern: "Name (ca. YYYY-YYYY BC)" or "Name (YYYY-YYYY BC)"
    m = re.match(
        r"^(.+?)\s*\((?:ca\.?\s+)?(\d+)[-–](\d+)\s+(BC|AD)\)\s*$", clean, re.IGNORECASE
    )
    if m:
        name = m.group(1).strip()
        y1 = int(m.group(2))
        y2 = int(m.group(3))
        era = m.group(4).upper()
        # AD dates are stored as negative BCE (or we could store as positive and note era)
        # Store BC as positive, AD as negative
        start = y1 if era == "BC" else -y1
        end = y2 if era == "BC" else -y2
        return {"raw": raw, "canonical": name, "start": start, "end": end}

    # Pattern: "Name (ca. YYYY BC)" — single year
    m = re.match(r"^(.+?)\s*\((?:ca\.?\s+)?(\d+)\s+(BC|AD)\)\s*$", clean, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        y = int(m.group(2))
        era = m.group(3).upper()
        val = y if era == "BC" else -y
        return {"raw": raw, "canonical": name, "start": val, "end": val}

    # No date found — store as-is
    return {"raw": raw, "canonical": clean, "start": None, "end": None}


def parse_provenience(raw: str) -> dict | None:
    """
    Parse "Ancient (mod. Modern)" format.

    "Nippur (mod. Nuffar)"           → ancient="Nippur", modern="Nuffar"
    "uncertain (mod. uncertain)"     → ancient="uncertain", modern="uncertain"
    "Nippur (mod. Nuffar) ?"        → ancient="Nippur" (strip ?)
    "Nippur (mod. Nuffar) ?"        → same
    """
    raw = raw.strip()
    if not raw:
        return None

    clean = re.sub(r"\s*\?$", "", raw).strip()

    m = re.match(r"^(.+?)\s*\(mod\.\s+(.+?)\)\s*$", clean, re.IGNORECASE)
    if m:
        ancient = m.group(1).strip()
        modern = m.group(2).strip()
        return {"raw": raw, "ancient_name": ancient, "modern_name": modern}

    # No "mod." pattern — store ancient name only
    return {"raw": raw, "ancient_name": clean, "modern_name": None}


def normalize_genre(raw: str) -> str:
    """Normalize genre string to canonical form."""
    # Title-case the primary genre (before any semicolon)
    primary = raw.split(";")[0].strip()
    # Handle known case variants
    canonical_map = {
        "administrative": "Administrative",
        "legal": "Legal",
        "letter": "Letter",
        "lexical": "Lexical",
        "literary": "Literary",
        "school": "School",
        "scientific": "Scientific",
        "administative": "Administrative",  # typo in source
        "omens": "Omen",
    }
    return canonical_map.get(
        primary.lower(), primary.title() if primary.islower() else primary
    )


def audit_csv() -> tuple[Counter, Counter, Counter, Counter]:
    """Read CDLI CSV and count distinct values per dimension."""
    periods: Counter = Counter()
    languages: Counter = Counter()
    genres: Counter = Counter()
    proveniences: Counter = Counter()

    with open(CDLI_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["period"].strip():
                periods[row["period"].strip()] += 1
            if row["language"].strip():
                for lang in row["language"].strip().split("; "):
                    if lang.strip():
                        languages[lang.strip()] += 1
            if row["genre"].strip():
                genres[row["genre"].strip()] += 1
            if row["provenience"].strip():
                proveniences[row["provenience"].strip()] += 1

    return periods, languages, genres, proveniences


def seed_periods(conn: psycopg.Connection, periods: Counter, dry_run: bool) -> int:
    inserted = 0
    seen_canonicals: dict[str, dict] = {}

    for raw, _ in periods.most_common():
        parsed = parse_period(raw)
        if not parsed:
            continue

        canonical = parsed["canonical"]
        start = parsed["start"]
        end = parsed["end"]

        # If we've seen this canonical before, use its dates (from the unqualified form)
        if canonical in seen_canonicals:
            existing = seen_canonicals[canonical]
            if start is None:
                start = existing["start"]
            if end is None:
                end = existing["end"]
        else:
            seen_canonicals[canonical] = {"start": start, "end": end}

        if not dry_run:
            conn.execute(
                """
                INSERT INTO period_canon (raw_period, canonical, date_start_bce, date_end_bce)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (raw_period) DO NOTHING
            """,
                (raw, canonical, start, end),
            )
        inserted += 1

    return inserted


def seed_languages(conn: psycopg.Connection, dry_run: bool) -> int:
    for cdli_name, oracc_code, full_name, family in LANGUAGE_MAP:
        if not dry_run:
            conn.execute(
                """
                INSERT INTO language_map (cdli_name, oracc_code, full_name, family)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (cdli_name) DO NOTHING
            """,
                (cdli_name, oracc_code, full_name, family),
            )
    return len(LANGUAGE_MAP)


def seed_genres(conn: psycopg.Connection, genres: Counter, dry_run: bool) -> int:
    inserted = 0
    for raw, _ in genres.most_common():
        canonical = normalize_genre(raw)
        if not dry_run:
            conn.execute(
                """
                INSERT INTO genre_canon (raw_genre, canonical)
                VALUES (%s, %s)
                ON CONFLICT (raw_genre) DO NOTHING
            """,
                (raw, canonical),
            )
        inserted += 1
    return inserted


def seed_proveniences(
    conn: psycopg.Connection, proveniences: Counter, dry_run: bool
) -> int:
    inserted = 0
    for raw, _ in proveniences.most_common():
        parsed = parse_provenience(raw)
        if not parsed:
            continue
        if not dry_run:
            conn.execute(
                """
                INSERT INTO provenience_canon (raw_provenience, ancient_name, modern_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (raw_provenience) DO NOTHING
            """,
                (raw, parsed["ancient_name"], parsed["modern_name"]),
            )
        inserted += 1
    return inserted


def seed_surfaces(conn: psycopg.Connection, dry_run: bool) -> int:
    for raw, canonical in SURFACE_CANON:
        if not dry_run:
            conn.execute(
                """
                INSERT INTO surface_canon (raw_surface, canonical)
                VALUES (%s, %s)
                ON CONFLICT (raw_surface) DO NOTHING
            """,
                (raw, canonical),
            )
    return len(SURFACE_CANON)


def main():
    parser = argparse.ArgumentParser(description="Seed normalization lookup tables")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate without writing"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 1: SEED LOOKUP TABLES")
    print("=" * 60)

    print("\nAuditing CDLI CSV...", end=" ", flush=True)
    periods, languages, genres, proveniences = audit_csv()
    print(
        f"done. Found {len(periods)} periods, {len(languages)} languages, "
        f"{len(genres)} genres, {len(proveniences)} proveniences."
    )

    if args.dry_run:
        print("\n[DRY RUN] No database writes.")
        conn = None
    else:
        settings = get_settings()
        conninfo = (
            f"host={settings.db_host} port={settings.db_port} "
            f"dbname={settings.db_name} user={settings.db_user} "
            f"password={settings.db_password}"
        )
        conn = psycopg.connect(conninfo)

    try:
        n_periods = seed_periods(conn, periods, args.dry_run)
        print(f"  period_canon:      {n_periods} rows")

        n_languages = seed_languages(conn, args.dry_run)
        print(f"  language_map:      {n_languages} rows")

        n_genres = seed_genres(conn, genres, args.dry_run)
        print(f"  genre_canon:       {n_genres} rows")

        n_proveniences = seed_proveniences(conn, proveniences, args.dry_run)
        print(f"  provenience_canon: {n_proveniences} rows")

        n_surfaces = seed_surfaces(conn, args.dry_run)
        print(f"  surface_canon:     {n_surfaces} rows")

        if conn and not args.dry_run:
            conn.commit()

        total = n_periods + n_languages + n_genres + n_proveniences + n_surfaces
        print(
            f"\n{'[DRY RUN] Would insert' if args.dry_run else 'Inserted'} {total} total rows."
        )

        # Validate against expected thresholds
        assert len(periods) >= 75, f"Expected >=75 periods, got {len(periods)}"
        assert len(languages) >= 30, f"Expected >=30 languages, got {len(languages)}"
        assert len(genres) >= 50, f"Expected >=50 genres, got {len(genres)}"
        assert (
            len(proveniences) >= 400
        ), f"Expected >=400 proveniences, got {len(proveniences)}"
        print("Validation: OK")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\nFailed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
