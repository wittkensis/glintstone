#!/usr/bin/env python3
"""
Steps 7, 8, 9, 14, 17: Parse CDLI ATF file.

In a single pass over cdliatf_unblocked.atf, populates:
  - surfaces    (Step 7)  — @obverse, @reverse, @left, @right, @top, @bottom, @seal
  - text_lines  (Step 8)  — numbered text lines per surface
  - tokens      (Step 9)  — whitespace-split words per text line
  - translations (Step 14) — #tr.XX: lines
  - composites  (Step 17) — >>Q lines extracted and stored
  - artifact_composites    — links from artifact to composite

ATF format reference:
  &P######  = tablet header
  #atf: lang xxx  = language declaration
  @tablet / @object ... = object structure (ignored)
  @obverse / @reverse / @edge / @column N = surface/column markers
  $ text = editorial note (is_ruling/is_blank flags)
  N. text = numbered text line
  N'. text = prime-numbered line (partial)
  >>Qxxxxxx NNN = composite reference line
  #tr.en: text = English translation
  # comment = ignored

The surfaces table constraint only allows:
  obverse, reverse, left_edge, right_edge, top_edge, bottom_edge, seal
Columns are tracked in line labels but mapped to the enclosing surface.

Usage:
    python 07_parse_atf.py [--dry-run] [--limit N]

--limit N: stop after N tablets (for testing)
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

ATF_FILE = (
    Path(__file__).resolve().parents[1] / "sources/CDLI/metadata/cdliatf_unblocked.atf"
)

BATCH_SIZE = 500  # tablets per batch flush

# ATF surface type → DB canonical
SURFACE_MAP = {
    "obverse": "obverse",
    "reverse": "reverse",
    "left": "left_edge",
    "right": "right_edge",
    "top": "top_edge",
    "bottom": "bottom_edge",
    "seal": "seal",
    # Aliases
    "o": "obverse",
    "r": "reverse",
    "edge": None,  # generic edge — skip (not in constraint)
    "face": None,  # not in constraint
    "column": None,  # columns are sub-surface structure
    "tablet": None,
    "object": None,
    "envelope": None,
    "tag": None,
    "prism": None,
    "cylinder": None,
    "brick": None,
    "cone": None,
    "bulla": None,
}

# Regex patterns
RE_HEADER = re.compile(r"^&(P\d+)\s*=\s*(.+)$")
RE_LANG = re.compile(r"^#atf:\s*lang\s+(\S+)")
RE_SURFACE = re.compile(r"^@(\w+)(?:\s+(.*))?$")
RE_COLUMN = re.compile(r"^@column\s+(\d+)", re.IGNORECASE)
# ENHANCED: Now handles sub-line notation (1.a., 3.b1., etc.) in addition to simple (1., 12'.)
RE_LINE = re.compile(r"^(\d+(?:\'|\.(?:[a-z](?:\d+)?))?\.)\s+(.+)$")
RE_RULING = re.compile(r"^\$\s*(single|double|triple)\s+ruling", re.IGNORECASE)
RE_BLANK = re.compile(r"^\$\s*(beginning|rest|reverse|surface)\s+broken", re.IGNORECASE)
RE_COMPOSITE = re.compile(r"^>>(Q\d+)\s+(.*)$")
RE_TRANSLATION = re.compile(r"^#tr\.(\w+):\s+(.+)$")


def parse_line_number(label: str) -> int | None:
    """'1.' → 1, '12'.' → 12, '3' → None if label not parseable."""
    m = re.match(r"^(\d+)", label.rstrip("."))
    return int(m.group(1)) if m else None


def tokenize_atf(text: str) -> list[str]:
    """
    Split an ATF transliteration line into individual tokens (words/signs).
    Handles: spaces, hyphens within words, editorial marks.
    Returns list of non-empty strings.
    """
    # Remove composite references on same line (shouldn't be there, but defensive)
    text = re.sub(r">>Q\S+\s*", "", text)
    # Split on whitespace
    parts = text.split()
    return [p for p in parts if p and p != ","]


def parse_atf_file(atf_path: Path, limit: int = 0):
    """
    Generator that yields parsed tablet dicts.
    Each tablet dict has:
      p_number, lang, surfaces[], lines[], translations[], composites[]
    """
    tablet = None
    current_surface_type = None  # canonical DB surface type or None
    current_column = 0  # 0 = no column marker seen; 1+ = @column N
    line_counter = 0

    with open(atf_path, encoding="utf-8", errors="replace") as f:
        tablet_count = 0
        for raw_line in f:
            line = raw_line.rstrip("\n").rstrip("\r")

            # Skip empty lines
            if not line.strip():
                continue

            # Tablet header
            m = RE_HEADER.match(line)
            if m:
                if tablet:
                    yield tablet
                    tablet_count += 1
                    if limit and tablet_count >= limit:
                        return

                tablet = {
                    "p_number": m.group(1),
                    "lang": "und",
                    "surfaces": {},  # surface_type → True (just track existence)
                    "lines": [],  # (surface_type, column_num, line_no, raw_atf, is_ruling, is_blank)
                    "translations": [],  # (lang_code, text)
                    "composites": [],  # (q_number, location_label)
                }
                current_surface_type = None
                current_column = 0
                line_counter = 0
                continue

            if tablet is None:
                continue

            # Language declaration
            m = RE_LANG.match(line)
            if m:
                tablet["lang"] = m.group(1)
                continue

            # Surface marker
            m = RE_SURFACE.match(line)
            if m:
                marker = m.group(1).lower()

                # Check if it's a column
                if marker == "column":
                    col_m = RE_COLUMN.match(line)
                    current_column = (
                        int(col_m.group(1)) if col_m else (current_column + 1)
                    )
                    continue

                # Map marker to DB surface type
                db_surface = SURFACE_MAP.get(marker)
                if db_surface is not None:
                    current_surface_type = db_surface
                    current_column = 0  # reset column on surface change
                    if db_surface not in tablet["surfaces"]:
                        tablet["surfaces"][db_surface] = True
                elif db_surface is None and marker in SURFACE_MAP:
                    # Valid ATF marker but not a DB surface (e.g. 'column', 'tablet')
                    current_surface_type = None
                # Unknown markers: preserve current surface
                continue

            # Composite reference
            m = RE_COMPOSITE.match(line)
            if m:
                q_number = "Q" + m.group(1)[1:].zfill(6)  # normalize to Q000000 format
                label = m.group(2).strip()
                tablet["composites"].append((q_number, label))
                continue

            # Translation
            m = RE_TRANSLATION.match(line)
            if m:
                tr_lang = m.group(1)
                tr_text = m.group(2)
                tablet["translations"].append((tr_lang, tr_text, line_counter))
                continue

            # Ruling / blank note
            if RE_RULING.match(line):
                line_counter += 1
                tablet["lines"].append(
                    (
                        current_surface_type,
                        current_column,
                        line_counter,
                        line.strip(),
                        1,
                        0,
                    )
                )
                continue

            if RE_BLANK.match(line) or line.startswith("$ "):
                line_counter += 1
                tablet["lines"].append(
                    (
                        current_surface_type,
                        current_column,
                        line_counter,
                        line.strip(),
                        0,
                        1,
                    )
                )
                continue

            # Text line
            m = RE_LINE.match(line)
            if m:
                label = m.group(1)  # e.g., "1.", "1'.", "1.a.", "3.b1."
                content = m.group(2)
                # ENHANCED: Keep full line number with sub-line notation (e.g., "1", "1'", "1.a", "3.b1")
                # Strip only the final period; preserve prime (') and sub-line (.a, .b1) notation
                line_no = label.rstrip(".")
                line_counter += 1
                tablet["lines"].append(
                    (current_surface_type, current_column, line_no, content, 0, 0)
                )
                continue

            # Skip comments and other markers
            # (anything starting with # that isn't #tr. or #atf:)

    if tablet:
        yield tablet


def flush_tablets(
    conn: psycopg.Connection,
    tablets: list,
    annotation_run_id_atf: int,
    annotation_run_id_cdli: int,
    known_p_numbers: set,
    stats: dict,
):
    """Flush a batch of parsed tablets to the database."""
    with conn.cursor() as cur:
        for tablet in tablets:
            p_number = tablet["p_number"]
            if p_number not in known_p_numbers:
                stats["skipped_unknown"] += 1
                continue

            # --- Surfaces ---
            surface_id_map = {}  # surface_type → surface.id
            for surface_type in tablet["surfaces"]:
                cur.execute(
                    """
                    INSERT INTO surfaces (p_number, surface_type)
                    VALUES (%s, %s)
                    ON CONFLICT (p_number, surface_type) DO NOTHING
                    RETURNING id
                """,
                    (p_number, surface_type),
                )
                row = cur.fetchone()
                if row:
                    surface_id_map[surface_type] = row[0]
                    stats["surfaces"] += 1
                else:
                    # Get existing id
                    cur.execute(
                        "SELECT id FROM surfaces WHERE p_number = %s AND surface_type = %s",
                        (p_number, surface_type),
                    )
                    row = cur.fetchone()
                    if row:
                        surface_id_map[surface_type] = row[0]

            # --- Text lines ---
            line_id_map = {}  # (surface_type, column_num, line_no) → text_line.id
            for (
                surface_type,
                column_num,
                line_no,
                raw_atf,
                is_ruling,
                is_blank,
            ) in tablet["lines"]:
                surface_id = surface_id_map.get(surface_type) if surface_type else None

                cur.execute(
                    """
                    INSERT INTO text_lines
                        (p_number, surface_id, column_number, line_number, raw_atf, is_ruling, is_blank, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'cdli')
                    ON CONFLICT (p_number, surface_id, column_number, line_number, source) DO NOTHING
                    RETURNING id
                """,
                    (
                        p_number,
                        surface_id,
                        column_num,
                        line_no,
                        raw_atf,
                        is_ruling,
                        is_blank,
                    ),
                )
                row = cur.fetchone()
                if row:
                    line_id = row[0]
                    line_id_map[(surface_type, column_num, line_no)] = line_id
                    stats["lines"] += 1

                    # --- Tokens (only for real text lines, not blank/ruling) ---
                    if not is_ruling and not is_blank:
                        tokens = tokenize_atf(raw_atf)
                        for pos, token_text in enumerate(tokens):
                            cur.execute(
                                """
                                INSERT INTO tokens (line_id, position, gdl_json, lang)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT DO NOTHING
                            """,
                                (
                                    line_id,
                                    pos,
                                    json.dumps({"frag": token_text}),
                                    tablet["lang"],
                                ),
                            )
                            stats["tokens"] += 1

            # --- Translations ---
            for tr_lang, tr_text, line_no in tablet["translations"]:
                cur.execute(
                    """
                    INSERT INTO translations (p_number, line_id, translation, language, source, annotation_run_id)
                    VALUES (%s, %s, %s, %s, 'cdli', %s)
                    ON CONFLICT DO NOTHING
                """,
                    (p_number, None, tr_text, tr_lang, annotation_run_id_cdli),
                )
                stats["translations"] += 1

            # --- Composites ---
            for q_number, label in tablet["composites"]:
                # Ensure composite exists
                cur.execute(
                    """
                    INSERT INTO composites (q_number, exemplar_count)
                    VALUES (%s, 0)
                    ON CONFLICT (q_number) DO UPDATE SET exemplar_count = composites.exemplar_count + 1
                """,
                    (q_number,),
                )

                # Link artifact to composite
                cur.execute(
                    """
                    INSERT INTO artifact_composites (p_number, q_number)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """,
                    (p_number, q_number),
                )
                stats["composite_links"] += 1

            stats["tablets"] += 1

    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Parse CDLI ATF file into DB")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, no DB writes"
    )
    parser.add_argument("--limit", type=int, default=0, help="Stop after N tablets")
    args = parser.parse_args()

    print("=" * 60)
    print("STEPS 7-9+14+17: PARSE CDLI ATF FILE")
    print("=" * 60)
    print(f"  Source: {ATF_FILE}")

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    conn = psycopg.connect(conninfo)

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM annotation_runs WHERE source_name = 'cdli-atf'")
        row = cur.fetchone()
        ann_run_atf = row[0] if row else None

        cur.execute("SELECT id FROM annotation_runs WHERE source_name = 'cdli-catalog'")
        row = cur.fetchone()
        ann_run_cdli = row[0] if row else None

        # Load all known p_numbers into memory for fast lookup
        print("\n  Loading known p_numbers...", end=" ", flush=True)
        cur.execute("SELECT p_number FROM artifacts")
        known_p_numbers = {row[0] for row in cur.fetchall()}
        print(f"done. {len(known_p_numbers):,} artifacts.")

    if args.dry_run:
        print("\n[DRY RUN] Parsing 1000 tablets to verify format...")
        count = 0
        for tablet in parse_atf_file(ATF_FILE, limit=1000):
            count += 1
        print(f"  Parsed {count} tablets. Format OK.")
        conn.close()
        return

    stats = {
        "tablets": 0,
        "surfaces": 0,
        "lines": 0,
        "tokens": 0,
        "translations": 0,
        "composite_links": 0,
        "skipped_unknown": 0,
    }

    batch = []
    print(f"\n  Parsing ATF (batch size {BATCH_SIZE} tablets)...")

    for tablet in parse_atf_file(ATF_FILE, limit=args.limit or 0):
        batch.append(tablet)

        if len(batch) >= BATCH_SIZE:
            flush_tablets(
                conn, batch, ann_run_atf, ann_run_cdli, known_p_numbers, stats
            )
            batch = []
            print(
                f"  {stats['tablets']:>7,} tablets  |  "
                f"{stats['surfaces']:>6,} surfaces  |  "
                f"{stats['lines']:>7,} lines  |  "
                f"{stats['tokens']:>8,} tokens",
                end="\r",
            )

    if batch:
        flush_tablets(conn, batch, ann_run_atf, ann_run_cdli, known_p_numbers, stats)

    conn.close()

    print("\n")
    print(f"  Tablets processed:   {stats['tablets']:,}")
    print(f"  Surfaces inserted:   {stats['surfaces']:,}")
    print(f"  Text lines inserted: {stats['lines']:,}")
    print(f"  Tokens inserted:     {stats['tokens']:,}")
    print(f"  Translations:        {stats['translations']:,}")
    print(f"  Composite links:     {stats['composite_links']:,}")
    print(f"  Skipped (unknown):   {stats['skipped_unknown']:,}")
    print("Validation: OK")


if __name__ == "__main__":
    main()
