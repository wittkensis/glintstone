#!/usr/bin/env python3
"""
Step 10: Import token readings from tokens.gdl_json (Phase A - minimal format).

Parses the minimal {"frag": "word"} format currently stored in tokens.gdl_json
and extracts form, reading, sign_function, and damage markers.

This is Phase A using ATF-derived data. Phase B (future) will re-import from
full ORACC CDL GDL arrays for higher precision.

Depends on:
  - Step 7-9 (tokens table populated with gdl_json)
  - Step 2 (annotation_runs table)

Usage:
    python 10_import_token_readings.py [--reset] [--limit N]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from psycopg.rows import dict_row
from core.config import get_settings

# Add citations/lib to path for checkpoint
citations_lib = Path(__file__).parent / "citations" / "lib"
sys.path.insert(0, str(citations_lib))

from checkpoint import ImportCheckpoint  # noqa: E402


def parse_minimal_gdl(gdl_json_str: str) -> dict | None:
    """
    Parse minimal {"frag": "word"} format from ATF parser.

    Returns dict with:
        form, reading, sign_function, damage, confidence
    or None if parsing fails.
    """
    try:
        data = json.loads(gdl_json_str)
        form = data.get("frag", "").strip()

        if not form:
            return None

        # Derive reading (heuristic: uppercase for display)
        reading = form.upper()

        # Infer sign_function from orthographic patterns
        if form.isupper():
            # All uppercase → likely logogram (NINDA, E₂)
            sign_function = "logographic"
        elif any(c.isdigit() for c in form):
            # Contains digits → likely numeric (1(geš₂), 3(aš))
            sign_function = "numeric"
        else:
            # Mixed/lowercase → syllabic (za, ba₄, lu₂)
            sign_function = "syllabographic"

        # Detect damage from ATF notation
        damage = "intact"
        if "#" in form:
            # Damaged sign marker
            damage = "damaged"
        elif "[" in form or "]" in form:
            # Broken/missing section
            damage = "missing"
        elif "!" in form or "?" in form:
            # Uncertain or collation marker
            damage = "illegible"

        return {
            "form": form,
            "reading": reading,
            "sign_function": sign_function,
            "damage": damage,
            "confidence": 0.7,  # Moderate confidence (ATF-derived heuristic)
        }

    except (json.JSONDecodeError, AttributeError, KeyError):
        return None


def main(args):
    settings = get_settings()

    # Connect to database
    conn = psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}",
        row_factory=dict_row,
    )

    # Initialize checkpoint
    checkpoint = ImportCheckpoint("10_token_readings", reset=args.reset)

    print(f"{'=' * 80}")
    print("STEP 10: Token Readings Import (Phase A - Minimal GDL)")
    print(f"{'=' * 80}\n")

    # Get or create annotation_run for this import
    run = conn.execute("""
        SELECT id FROM annotation_runs
        WHERE source_name = 'cdli-atf-minimal'
        LIMIT 1
    """).fetchone()

    if run:
        run_id = run["id"]
        print(f"Using existing annotation_run: id={run_id}")
    else:
        run_id = conn.execute("""
            INSERT INTO annotation_runs (
                source_name, source_type, method, notes, created_at
            ) VALUES (
                'cdli-atf-minimal', 'import', 'import',
                'Phase A: Token readings from ATF fragments (heuristic parsing)',
                NOW()
            ) RETURNING id
        """).fetchone()["id"]
        conn.commit()
        print(f"Created new annotation_run: id={run_id}")

    # Get total token count
    total = conn.execute("""
        SELECT COUNT(*) as cnt FROM tokens WHERE gdl_json IS NOT NULL
    """).fetchone()["cnt"]

    checkpoint.set_total(total)
    print(f"Total tokens to process: {total:,}\n")

    # Process tokens in batches
    offset = checkpoint.resume_offset
    batch_size = 10000
    commit_interval = 50000

    while True:
        # Fetch batch
        tokens = conn.execute(
            """
            SELECT id, gdl_json FROM tokens
            WHERE gdl_json IS NOT NULL
            ORDER BY id
            LIMIT %s OFFSET %s
        """,
            (batch_size, offset),
        ).fetchall()

        if not tokens:
            break

        # Parse and prepare batch for insert
        batch = []
        for token in tokens:
            parsed = parse_minimal_gdl(token["gdl_json"])
            if parsed:
                batch.append(
                    (
                        token["id"],  # token_id
                        parsed["form"],  # form
                        parsed["reading"],  # reading
                        parsed["sign_function"],  # sign_function
                        parsed["damage"],  # damage
                        parsed["confidence"],  # confidence
                        run_id,  # annotation_run_id
                        1,  # is_consensus (Phase A default)
                    )
                )

        # Batch insert
        if batch:
            with conn.cursor() as cur:
                for row in batch:
                    cur.execute(
                        """
                        INSERT INTO token_readings (
                            token_id, form, reading, sign_function,
                            damage, confidence, annotation_run_id, is_consensus
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        row,
                    )

        # Update stats
        checkpoint.stats["processed"] += len(tokens)
        checkpoint.stats["inserted"] += len(batch)
        if len(batch) < len(tokens):
            checkpoint.stats["skipped"] += len(tokens) - len(batch)

        offset += batch_size

        # Periodic commit and progress report
        if offset % commit_interval == 0 or checkpoint.interrupted:
            conn.commit()
            checkpoint.save()
            checkpoint.print_progress(offset, total)

        if checkpoint.interrupted:
            print("\nInterrupted. Progress saved. Resume with same command.")
            break

        if args.limit and offset >= args.limit:
            print(f"\n--limit {args.limit} reached")
            break

    # Final commit
    conn.commit()

    # Mark completion
    if not checkpoint.interrupted and not args.limit:
        checkpoint.save(completed=True)

    checkpoint.print_summary()

    # Validation checks
    print(f"\n{'-' * 80}")
    print("VALIDATION")
    print(f"{'-' * 80}")

    result = conn.execute("SELECT COUNT(*) as cnt FROM token_readings").fetchone()
    print(f"Total token_readings inserted: {result['cnt']:,}")

    orphans = conn.execute("""
        SELECT COUNT(*) as cnt FROM tokens t
        LEFT JOIN token_readings tr ON t.id = tr.token_id
        WHERE t.gdl_json IS NOT NULL AND tr.id IS NULL
    """).fetchone()
    print(f"Orphaned tokens (no reading): {orphans['cnt']:,}")

    damage_dist = conn.execute("""
        SELECT damage, COUNT(*) as cnt FROM token_readings
        GROUP BY damage ORDER BY cnt DESC
    """).fetchall()
    print("\nDamage distribution:")
    for d in damage_dist:
        print(f"  {d['damage']}: {d['cnt']:,}")

    sign_func_dist = conn.execute("""
        SELECT sign_function, COUNT(*) as cnt FROM token_readings
        GROUP BY sign_function ORDER BY cnt DESC
    """).fetchall()
    print("\nSign function distribution:")
    for s in sign_func_dist:
        print(f"  {s['sign_function']}: {s['cnt']:,}")

    conn.close()

    print(f"\n{'=' * 80}")
    print("STEP 10 COMPLETE")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import token readings (Phase A)")
    parser.add_argument(
        "--reset", action="store_true", help="Start fresh, discarding checkpoint"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of tokens (for testing)"
    )
    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
