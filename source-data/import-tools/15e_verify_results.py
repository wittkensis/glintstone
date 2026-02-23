#!/usr/bin/env python3
"""Verify Phase 3 import results."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

settings = get_settings()
conn = psycopg.connect(
    f"host={settings.db_host} port={settings.db_port} "
    f"dbname={settings.db_name} user={settings.db_user} "
    f"password={settings.db_password}"
)

print("=" * 80)
print("VERIFICATION RESULTS")
print("=" * 80)
print()

# Sign counts
sign_count = conn.execute(
    "SELECT COUNT(*) FROM lexical_signs WHERE source = 'epsd2-sl'"
).fetchone()[0]
unique_signs = conn.execute(
    "SELECT COUNT(DISTINCT sign_name) FROM lexical_signs WHERE source = 'epsd2-sl'"
).fetchone()[0]
print(f"Signs (total):                      {sign_count:,}")
print(f"Signs (unique names):               {unique_signs:,}")

# Association counts
assoc_count = conn.execute(
    "SELECT COUNT(*) FROM lexical_sign_lemma_associations WHERE source = 'epsd2-sl'"
).fetchone()[0]
assoc_with_values = conn.execute(
    "SELECT COUNT(*) FROM lexical_sign_lemma_associations WHERE source = 'epsd2-sl' AND value IS NOT NULL"
).fetchone()[0]
print(f"Sign-Lemma associations:            {assoc_count:,}")
print(f"  └─ With values populated:         {assoc_with_values:,}")

# Lemma/sense counts
lemma_count = conn.execute(
    "SELECT COUNT(*) FROM lexical_lemmas WHERE source = 'epsd2'"
).fetchone()[0]
sense_count = conn.execute(
    "SELECT COUNT(*) FROM lexical_senses WHERE source = 'epsd2'"
).fetchone()[0]
print(f"Lemmas:                             {lemma_count:,}")
print(f"Senses:                             {sense_count:,}")

print()
print("=" * 80)
print("COMPARISON TO PREVIOUS")
print("=" * 80)
print()
print("Previous associations:              2,325")
print(f"New associations:                   {assoc_count:,}")
improvement = assoc_count - 2325
improvement_pct = improvement / 2325 * 100
print(f"Improvement:                        +{improvement:,} ({improvement_pct:.1f}%)")
print()
print("Expected improvement:               ~400 (from case-insensitive)")
print(f"Actual improvement:                 {improvement:,}")

if improvement >= 400:
    print(f"\n✓ Exceeded expectations! (+{improvement - 400:,} more than expected)")
elif improvement >= 300:
    print(f"\n✓ Close to expectations (within {400 - improvement:,})")
else:
    print(f"\n⚠ Below expectations (missing {400 - improvement:,})")

print()

# Sample associations with subscripts
print("=" * 80)
print("SAMPLE ASSOCIATIONS (with subscripts preserved):")
print("=" * 80)
print()

with conn.cursor() as cur:
    cur.execute(
        """
        SELECT
            ls.sign_name,
            sla.value,
            ll.citation_form,
            ll.guide_word,
            ll.pos
        FROM lexical_sign_lemma_associations sla
        JOIN lexical_signs ls ON sla.sign_id = ls.id
        JOIN lexical_lemmas ll ON sla.lemma_id = ll.id
        WHERE sla.source = 'epsd2-sl'
          AND sla.value ~ '[₀-₉]'
        LIMIT 10
        """
    )
    samples = cur.fetchall()

    for s in samples:
        sign_name, value, citation_form, guide_word, pos = s
        print(f"  {sign_name:15} → {value:15} → {citation_form}[{guide_word}]{pos}")

# Check for proper nouns (case-insensitive matches)
print()
print("=" * 80)
print("SAMPLE PROPER NOUN MATCHES (case-insensitive):")
print("=" * 80)
print()

with conn.cursor() as cur:
    cur.execute(
        """
        SELECT
            ls.sign_name,
            sla.value,
            ll.citation_form,
            ll.guide_word,
            ll.pos
        FROM lexical_sign_lemma_associations sla
        JOIN lexical_signs ls ON sla.sign_id = ls.id
        JOIN lexical_lemmas ll ON sla.lemma_id = ll.id
        WHERE sla.source = 'epsd2-sl'
          AND ll.pos IN ('DN', 'PN', 'GN', 'SN', 'WN')
        LIMIT 10
        """
    )
    proper_nouns = cur.fetchall()

    if proper_nouns:
        for s in proper_nouns:
            sign_name, value, citation_form, guide_word, pos = s
            print(f"  {sign_name:15} → {value:15} → {citation_form}[{guide_word}]{pos}")
    else:
        print("  (No proper noun associations found)")

conn.close()

print()
print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
