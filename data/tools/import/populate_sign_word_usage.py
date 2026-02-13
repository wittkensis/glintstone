#!/usr/bin/env python3
"""
Populate Sign-Word Usage Table (v2)

Analyzes lemma FORMS (actual tablet spellings) to map cuneiform signs to
glossary entries. Also populates signs.sign_type and signs.most_common_value.

Previous version parsed citation_form (word transliterations) which missed
82% of signs. This version:
  - Uses lemmas.form for sign extraction (actual tablet spellings)
  - Handles compound signs (|A.AN|, |LAGAB×U|)
  - Decomposes compounds to credit component signs
  - Matches uppercase tokens as sign IDs, lowercase as sign values

Usage:
    python3 populate_sign_word_usage.py [--dry-run]
"""

import sqlite3
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # -> CUNEIFORM/
DB_PATH = BASE_DIR / "database" / "glintstone.db"


# ---------------------------------------------------------------------------
# Sign type classification
# ---------------------------------------------------------------------------

def classify_sign_type(sign_id):
    """Classify sign as simple, compound, or variant based on sign_id format."""
    if '|' in sign_id:
        return 'compound'
    if '@' in sign_id:
        return 'variant'
    return 'simple'


def decompose_compound(sign_id):
    """
    Extract component sign IDs from a compound sign.

    Examples:
        |A.AN|     -> [A, AN]
        |LAGAB×U|  -> [LAGAB, U]
        |A.LAGAB×HAL.GAL| -> [A, LAGAB, HAL, GAL]
        |ZI&ZI.LAGAB| -> [ZI, LAGAB]

    Operators: . (beside), × (containing), & (over), % (crossing)
    """
    inner = sign_id.strip('|')
    if not inner:
        return []

    # Split on operators: . × & %
    parts = re.split(r'[.×&%]', inner)

    # Clean up: remove parentheses groupings, @modifiers, numeric prefixes
    components = []
    for part in parts:
        part = part.strip()
        part = re.sub(r'\(.*?\)', '', part)  # remove (...) groups
        part = re.sub(r'@\w+', '', part)     # remove @g, @t modifiers
        part = re.sub(r'~\w+', '', part)     # remove ~a, ~b modifiers
        part = part.strip()
        if part and not part.isdigit():
            components.append(part)

    return components


# ---------------------------------------------------------------------------
# Form parsing (extract sign tokens from lemma forms)
# ---------------------------------------------------------------------------

def normalize_subscript(text):
    """Convert Unicode subscript digits to ASCII: niŋ₂ -> niŋ2"""
    subscript_map = str.maketrans('₀₁₂₃₄₅₆₇₈₉', '0123456789')
    return text.translate(subscript_map)


def parse_form(form):
    """
    Extract sign tokens from a lemma form string.

    Returns list of dicts: {value, is_determinative, is_compound, raw}

    Handles:
        - Compound signs: |LAGAB×U|, |A.AN|
        - Inline compounds: sipad(|PA.LU|)
        - Determinatives: {d}, {ki}, {urud}
        - Hyphenated syllables: ka-la-am
        - Damage markers: #, ?, !
        - Subscripts: niŋ₂, lu₂
    """
    if not form or form == 'X' or form == 'x':
        return []

    tokens = []

    # Step 1: Extract compound sign references |...|
    # These may appear standalone or inline: sipad(|PA.LU|)
    compound_pattern = r'\|[^|]+\|'
    compounds_found = re.findall(compound_pattern, form)
    for comp in compounds_found:
        tokens.append({
            'value': comp,
            'is_determinative': False,
            'is_compound': True,
            'raw': comp,
        })

    # Remove compound references from form for further parsing
    remaining = re.sub(compound_pattern, '', form)

    # Step 2: Extract determinatives {d}, {ki}, {urud}, etc.
    det_pattern = r'\{([^}]+)\}'
    for det_match in re.finditer(det_pattern, remaining):
        det_content = det_match.group(1)
        # Skip phonetic glosses like {+ga}
        if det_content.startswith('+'):
            continue
        tokens.append({
            'value': det_content,
            'is_determinative': True,
            'is_compound': False,
            'raw': det_match.group(0),
        })

    # Remove determinatives and phonetic glosses
    remaining = re.sub(r'\{[^}]*\}', '', remaining)

    # Step 3: Remove damage markers, question marks, etc.
    remaining = re.sub(r'[#?!*]', '', remaining)

    # Step 4: Remove parenthetical glosses like (KASKAL)
    remaining = re.sub(r'\([^)]*\)', '', remaining)

    # Step 5: Split by hyphens into syllables
    remaining = remaining.strip()
    if remaining:
        parts = remaining.split('-')
        for part in parts:
            part = part.strip()
            if not part or part == 'x' or part == 'X':
                continue
            # Dot-separated uppercase tokens (EN.LIL₂, KU₃.BABBAR)
            # are compound sign references written without pipes
            if '.' in part and part == part.upper() and any(c.isalpha() for c in part):
                tokens.append({
                    'value': f'|{part}|',
                    'is_determinative': False,
                    'is_compound': True,
                    'raw': part,
                })
            else:
                tokens.append({
                    'value': part,
                    'is_determinative': False,
                    'is_compound': False,
                    'raw': part,
                })

    return tokens


# ---------------------------------------------------------------------------
# Sign matching
# ---------------------------------------------------------------------------

def build_sign_lookups(cursor):
    """
    Build lookup tables for matching tokens to signs.

    Returns:
        sign_ids: set of all sign_ids (uppercase)
        value_to_signs: dict mapping lowercase value -> list of sign_ids
        sign_id_lower: dict mapping lowercase sign_id -> sign_id
    """
    # All sign IDs
    cursor.execute("SELECT sign_id FROM signs")
    all_signs = {row['sign_id'] for row in cursor.fetchall()}
    sign_id_lower = {sid.lower(): sid for sid in all_signs}

    # All sign values -> sign_id mappings
    cursor.execute("SELECT sign_id, value FROM sign_values")
    value_to_signs = defaultdict(list)
    for row in cursor.fetchall():
        value_to_signs[row['value'].lower()].append(row['sign_id'])

    return all_signs, value_to_signs, sign_id_lower


def match_token_to_sign(token, all_sign_ids, value_to_signs, sign_id_lower):
    """
    Match a parsed token to one or more sign_ids.

    Strategy:
        1. Compound tokens: match whole token as sign_id, then decompose
        2. UPPERCASE tokens: try as sign_id first, then as value
        3. Lowercase/mixed: try as value first, then as sign_id
        4. Try with subscript normalization

    Returns list of (sign_id, matched_value) tuples.
    """
    value = token['value']
    matches = []

    if token['is_compound']:
        # Direct compound match
        compound_id = value  # e.g., |A.AN|
        if compound_id in all_sign_ids:
            matches.append((compound_id, value))

        # Also credit component signs
        components = decompose_compound(value)
        for comp in components:
            if comp in all_sign_ids:
                matches.append((comp, comp))
            elif comp.lower() in sign_id_lower:
                matches.append((sign_id_lower[comp.lower()], comp))

        return matches

    # Normalize subscripts for matching: niŋ₂ -> niŋ2
    normalized = normalize_subscript(value)
    value_lower = value.lower()
    normalized_lower = normalized.lower()

    # Check if it's an uppercase token (logographic sign name)
    is_upper = value == value.upper() and any(c.isalpha() for c in value)

    if is_upper:
        # Try as sign_id first
        if value in all_sign_ids:
            matches.append((value, value))
            return matches
        # Try case-insensitive sign_id
        if value_lower in sign_id_lower:
            sid = sign_id_lower[value_lower]
            matches.append((sid, value))
            return matches

    # Try as value (in sign_values table)
    for try_val in [value_lower, normalized_lower]:
        if try_val in value_to_signs:
            # Pick all matching signs (but prefer first/most common)
            for sid in value_to_signs[try_val]:
                matches.append((sid, try_val))
            return matches

    # Try as sign_id (case-insensitive)
    if value_lower in sign_id_lower:
        sid = sign_id_lower[value_lower]
        matches.append((sid, value))
        return matches

    # Try uppercase version as sign_id
    if value.upper() in all_sign_ids:
        matches.append((value.upper(), value))
        return matches

    return matches


def detect_value_type(token, is_single_sign_word):
    """Determine if sign is logographic, syllabic, or determinative."""
    if token['is_determinative']:
        return 'determinative'

    value = token['value']

    # Compound signs used as whole words are logographic
    if token['is_compound']:
        return 'logographic'

    # UPPERCASE tokens are typically logographic
    if value == value.upper() and any(c.isalpha() for c in value):
        return 'logographic'

    # Single-sign words where the sign IS the word are logographic
    if is_single_sign_word:
        return 'logographic'

    # Multi-syllable words: individual syllables are syllabic
    return 'syllabic'


# ---------------------------------------------------------------------------
# Main population logic
# ---------------------------------------------------------------------------

def populate_sign_word_usage(dry_run=False):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 60)
    print("Sign-Word Usage Population (v2)")
    print("=" * 60)
    print()

    # -----------------------------------------------------------------------
    # Step 1: Populate sign_type
    # -----------------------------------------------------------------------
    print("Step 1: Populating sign_type...")
    cursor.execute("SELECT sign_id FROM signs")
    type_counts = defaultdict(int)
    for row in cursor.fetchall():
        sign_type = classify_sign_type(row['sign_id'])
        type_counts[sign_type] += 1
        if not dry_run:
            cursor.execute(
                "UPDATE signs SET sign_type = ? WHERE sign_id = ?",
                (sign_type, row['sign_id'])
            )
    if not dry_run:
        conn.commit()
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print()

    # -----------------------------------------------------------------------
    # Step 2: Build sign lookup tables
    # -----------------------------------------------------------------------
    print("Step 2: Building sign lookups...")
    all_sign_ids, value_to_signs, sign_id_lower = build_sign_lookups(cursor)
    print(f"  {len(all_sign_ids)} sign IDs")
    print(f"  {len(value_to_signs)} unique values mapped")
    print()

    # -----------------------------------------------------------------------
    # Step 3: Build glossary entry lookup (cf + lang -> entry_id)
    # -----------------------------------------------------------------------
    print("Step 3: Loading glossary entries...")
    cursor.execute("""
        SELECT entry_id, citation_form, language
        FROM glossary_entries
        WHERE citation_form IS NOT NULL
    """)
    entry_lookup = {}
    for row in cursor.fetchall():
        key = (row['citation_form'], row['language'])
        entry_lookup[key] = row['entry_id']

    # Also build a language-family lookup (akk-x-stdbab -> akk)
    for row_key in list(entry_lookup.keys()):
        cf, lang = row_key
        if '-' in lang:
            base_lang = lang.split('-')[0]
            family_key = (cf, base_lang)
            if family_key not in entry_lookup:
                entry_lookup[family_key] = entry_lookup[row_key]

    print(f"  {len(entry_lookup)} cf+lang combinations")
    print()

    # -----------------------------------------------------------------------
    # Step 4: Process lemmas
    # -----------------------------------------------------------------------
    print("Step 4: Processing lemmas...")

    # Group lemmas by (cf, lang) for efficient processing
    cursor.execute("""
        SELECT form, cf, lang, COUNT(*) as occurrence_count
        FROM lemmas
        WHERE form IS NOT NULL AND cf IS NOT NULL AND lang IS NOT NULL
        GROUP BY form, cf, lang
    """)
    lemma_groups = cursor.fetchall()
    print(f"  {len(lemma_groups)} unique (form, cf, lang) combinations")

    # sign_word_usage accumulator: (sign_id, entry_id, sign_value) -> {count, value_type}
    usage_map = defaultdict(lambda: {'count': 0, 'value_type': None})
    unmatched_tokens = defaultdict(int)
    entries_not_found = defaultdict(int)
    matched_lemmas = 0
    total_lemmas = 0

    for lemma_row in lemma_groups:
        total_lemmas += 1
        form = lemma_row['form']
        cf = lemma_row['cf']
        lang = lemma_row['lang']
        count = lemma_row['occurrence_count']

        # Find glossary entry for this lemma
        entry_id = entry_lookup.get((cf, lang))
        if not entry_id:
            # Try base language
            base_lang = lang.split('-')[0] if '-' in lang else lang
            entry_id = entry_lookup.get((cf, base_lang))
        if not entry_id:
            entries_not_found[(cf, lang)] += count
            continue

        # Parse form into tokens
        tokens = parse_form(form)
        if not tokens:
            continue

        is_single_sign = len([t for t in tokens if not t['is_determinative']]) == 1

        # Match each token to signs
        form_had_match = False
        for token in tokens:
            matches = match_token_to_sign(
                token, all_sign_ids, value_to_signs, sign_id_lower
            )

            if not matches:
                unmatched_tokens[token['value']] += count
                continue

            form_had_match = True
            value_type = detect_value_type(token, is_single_sign)

            # Use first match (most likely) for the sign-word link
            # But for compounds, we add all component matches too
            for sign_id, matched_value in matches:
                key = (sign_id, entry_id, matched_value)
                usage_map[key]['count'] += count
                if usage_map[key]['value_type'] is None:
                    usage_map[key]['value_type'] = value_type

        if form_had_match:
            matched_lemmas += 1

        if total_lemmas % 10000 == 0:
            print(f"  Processed {total_lemmas}/{len(lemma_groups)}...")

    print(f"  Matched: {matched_lemmas}/{total_lemmas} lemma groups")
    print(f"  Unique sign-word combos: {len(usage_map)}")
    print(f"  Unmatched tokens: {len(unmatched_tokens)}")
    print(f"  Entries not found: {len(entries_not_found)}")
    print()

    # Show top unmatched
    if unmatched_tokens:
        top_unmatched = sorted(unmatched_tokens.items(), key=lambda x: -x[1])[:15]
        print("  Top unmatched tokens:")
        for tok, cnt in top_unmatched:
            print(f"    {tok}: {cnt}")
        print()

    # -----------------------------------------------------------------------
    # Step 5: Write to database
    # -----------------------------------------------------------------------
    if dry_run:
        print("DRY RUN: Would insert the following:")
        sample = list(usage_map.items())[:10]
        for (sign_id, entry_id, sign_value), data in sample:
            print(f"  {sign_id} + {entry_id} -> {sign_value} ({data['value_type']}) x{data['count']}")
        if len(usage_map) > 10:
            print(f"  ... and {len(usage_map) - 10} more")
    else:
        print("Step 5: Writing sign_word_usage table...")
        cursor.execute("DELETE FROM sign_word_usage")
        print("  Cleared existing data")

        inserted = 0
        for (sign_id, entry_id, sign_value), data in usage_map.items():
            cursor.execute("""
                INSERT OR REPLACE INTO sign_word_usage
                    (sign_id, sign_value, entry_id, usage_count, value_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                sign_id,
                sign_value,
                entry_id,
                data['count'],
                data['value_type'],
            ))
            inserted += 1
            if inserted % 5000 == 0:
                print(f"  Inserted {inserted}/{len(usage_map)}...")

        conn.commit()
        print(f"  Inserted {inserted} rows")

    # -----------------------------------------------------------------------
    # Step 6: Update most_common_value
    # -----------------------------------------------------------------------
    if not dry_run:
        print()
        print("Step 6: Updating most_common_value...")
        cursor.execute("""
            UPDATE signs SET most_common_value = (
                SELECT sv.value
                FROM sign_values sv
                LEFT JOIN sign_word_usage swu
                    ON sv.sign_id = swu.sign_id AND sv.value = swu.sign_value
                WHERE sv.sign_id = signs.sign_id
                ORDER BY COALESCE(swu.usage_count, 0) DESC, sv.value ASC
                LIMIT 1
            )
        """)
        conn.commit()
        updated = cursor.execute(
            "SELECT COUNT(*) FROM signs WHERE most_common_value IS NOT NULL"
        ).fetchone()[0]
        print(f"  Updated most_common_value for {updated} signs")

    # -----------------------------------------------------------------------
    # Step 7: Update sign_values.frequency
    # -----------------------------------------------------------------------
    if not dry_run:
        print()
        print("Step 7: Updating sign_values.frequency...")
        cursor.execute("""
            UPDATE sign_values SET frequency = COALESCE((
                SELECT SUM(swu.usage_count)
                FROM sign_word_usage swu
                WHERE swu.sign_id = sign_values.sign_id
                  AND swu.sign_value = sign_values.value
            ), 0)
        """)
        conn.commit()
        print("  Done")

    # -----------------------------------------------------------------------
    # Final stats
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    if not dry_run:
        cursor.execute("SELECT COUNT(*) FROM sign_word_usage")
        print(f"Total sign-word relationships: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(DISTINCT sign_id) FROM sign_word_usage")
        unique_signs = cursor.fetchone()[0]
        total_signs = cursor.execute("SELECT COUNT(*) FROM signs").fetchone()[0]
        print(f"Signs with usage: {unique_signs}/{total_signs} ({100*unique_signs/total_signs:.1f}%)")

        cursor.execute("SELECT COUNT(DISTINCT entry_id) FROM sign_word_usage")
        print(f"Words with sign links: {cursor.fetchone()[0]}")

        print()
        print("By value type:")
        cursor.execute("""
            SELECT value_type, COUNT(*) as cnt, SUM(usage_count) as total
            FROM sign_word_usage
            GROUP BY value_type
            ORDER BY total DESC
        """)
        for row in cursor.fetchall():
            print(f"  {row['value_type'] or 'unknown'}: {row['cnt']} combos, {row['total']} occurrences")

        print()
        print("By sign type:")
        cursor.execute("""
            SELECT s.sign_type, COUNT(DISTINCT s.sign_id) as total,
                   COUNT(DISTINCT swu.sign_id) as with_usage
            FROM signs s
            LEFT JOIN sign_word_usage swu ON s.sign_id = swu.sign_id
            GROUP BY s.sign_type
        """)
        for row in cursor.fetchall():
            pct = 100 * row['with_usage'] / row['total'] if row['total'] else 0
            print(f"  {row['sign_type']}: {row['with_usage']}/{row['total']} ({pct:.0f}%)")

    conn.close()
    print()
    print("Done!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate sign-word usage (v2)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without writing")
    args = parser.parse_args()

    populate_sign_word_usage(dry_run=args.dry_run)
