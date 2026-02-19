#!/usr/bin/env python3
"""
Step 4: Import OGSL sign list into signs and sign_values tables.

Source: source-data/sources/ORACC/ogsl/json/ogsl/ogsl-sl.json

Populates:
  - signs: one row per sign (sign_id = OGSL name, e.g. "A", "KA", "|A.B|")
  - sign_values: one row per phonetic reading per sign

sign_type classification:
  - simple:   no '|' wrapper, no '@' modifier
  - modified: contains '@' modifier (e.g. A@g, A@t)
  - compound: wrapped in '|...|' with components

Usage:
    python 04_import_signs.py [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from glintstone.config import get_settings

OGSL_JSON = (
    Path(__file__).resolve().parents[1]
    / "sources/ORACC/ogsl/json/ogsl/ogsl-sl.json"
)


def classify_sign(sign_id: str) -> str:
    if sign_id.startswith("|") and sign_id.endswith("|"):
        return "compound"
    if "@" in sign_id:
        return "modified"
    return "simple"


def parse_unicode_decimal(hex_str: str) -> int | None:
    """Parse 'x12000' or 'x12000.x12001' → decimal of first codepoint."""
    if not hex_str:
        return None
    first = hex_str.split(".")[0]
    try:
        return int(first.lstrip("x"), 16)
    except ValueError:
        return None


def clean_value(v: str) -> str:
    """Strip subscript numbers and special chars to get a clean reading."""
    return v.strip()


def extract_sub_index(v: str) -> int | None:
    """Try to extract the subscript number from a reading like 'a₂' → 2."""
    m = re.search(r'[₀₁₂₃₄₅₆₇₈₉]+$', v)
    if not m:
        # Try plain digits
        m = re.search(r'(\d+)$', v)
        if m:
            return int(m.group(1))
        return None
    subs = "₀₁₂₃₄₅₆₇₈₉"
    result = ""
    for c in m.group(0):
        idx = subs.find(c)
        if idx >= 0:
            result += str(idx)
    return int(result) if result else None


def infer_value_type(v: str) -> str:
    """
    Heuristic to classify a sign reading as syllabic, logographic, numeric, or determinative.
    Determinatives typically appear in brackets in running text but OGSL doesn't mark them here.
    For now: numeric if it matches digit patterns, syllabic if short consonant-vowel,
    else logographic.
    """
    clean = re.sub(r'[₀-₉\d]', '', v).strip()
    # Numeric if original is all digits/numerals
    if re.match(r'^[0-9\(\)]+$', v):
        return "numeric"
    # Short (1-4 char) lowercase = likely syllabic
    if len(clean) <= 4 and clean.islower():
        return "syllabic"
    # Uppercase = logographic
    if clean.isupper() and len(clean) >= 1:
        return "logographic"
    return "syllabic"


def main():
    parser = argparse.ArgumentParser(description="Import OGSL sign list")
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 4: IMPORT OGSL SIGNS")
    print("=" * 60)

    print(f"\n  Loading {OGSL_JSON}...", end=" ", flush=True)
    with open(OGSL_JSON, encoding="utf-8") as f:
        data = json.load(f)
    signs_data = data.get("signs", {})
    print(f"done. {len(signs_data)} sign entries.")

    if args.dry_run:
        print("\n[DRY RUN] No database writes.")
        sample = list(signs_data.items())[:5]
        for sid, sdata in sample:
            values = sdata.get("values", [])
            print(f"  {sid}: {values[:3]}")
        return

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )

    conn = psycopg.connect(conninfo)
    signs_inserted = 0
    signs_skipped = 0
    values_inserted = 0

    try:
        with conn.cursor() as cur:
            for sign_id, sign_data in signs_data.items():
                utf8 = sign_data.get("utf8")
                hex_str = sign_data.get("hex", "")
                uname = sign_data.get("uname")
                uphase = sign_data.get("uphase")
                sign_type = classify_sign(sign_id)
                unicode_decimal = parse_unicode_decimal(hex_str)

                # Serialize GDL definition as JSON string
                gdl = sign_data.get("gdl")
                gdl_json = json.dumps(gdl) if gdl else None

                # Most common value = first in values list
                values_list = sign_data.get("values", [])
                most_common = values_list[0] if values_list else None

                cur.execute("""
                    INSERT INTO signs (
                        sign_id, utf8, unicode_hex, unicode_decimal,
                        uname, uphase, sign_type, gdl_definition, most_common_value
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sign_id) DO NOTHING
                    RETURNING sign_id
                """, (
                    sign_id, utf8, hex_str if hex_str else None,
                    unicode_decimal, uname, uphase, sign_type, gdl_json, most_common
                ))
                row = cur.fetchone()
                if row:
                    signs_inserted += 1
                else:
                    signs_skipped += 1
                    continue  # Skip values for existing signs

                # Insert sign values (phonetic readings)
                for v in values_list:
                    value = clean_value(v)
                    if not value:
                        continue
                    sub_idx = extract_sub_index(value)
                    v_type = infer_value_type(value)

                    cur.execute("""
                        INSERT INTO sign_values (sign_id, value, sub_index, value_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (sign_id, value, sub_idx, v_type))
                    values_inserted += 1

            conn.commit()

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"\nFailed: {e}", file=sys.stderr)
        sys.exit(1)

    conn.close()

    print(f"\n  Signs inserted:  {signs_inserted}")
    print(f"  Signs skipped:   {signs_skipped}")
    print(f"  Values inserted: {values_inserted}")

    # Validate
    assert signs_inserted >= 1000, f"Expected >=1000 signs, got {signs_inserted}"
    print("Validation: OK")


if __name__ == "__main__":
    main()
