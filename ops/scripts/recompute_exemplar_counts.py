"""Global one-time recompute of composites.exemplar_count (#295).

Background
----------
The atf-parser writes an inflated ``composites.exemplar_count`` (it counts ATF
sub-records, not real linked witnesses). #293's ``oracc_composite_witnesses``
connector only RECOMPUTED the count for the Q-numbers it actually touched in a
given run, so every composite the connector never linked kept its inflated
atf-parser figure. Q000376, for example, advertised an inflated count while
having only 3 real witnesses.

This script does the authoritative GLOBAL fix in one statement: for EVERY
composite, set ``exemplar_count`` to the true ``COUNT(*)`` of its rows in
``artifact_composites`` (0 when it has none). A ``LEFT JOIN`` guarantees
zero-witness composites are reset to 0 rather than skipped.

Idempotent: re-running changes nothing (the count is stable, and the
``IS DISTINCT FROM`` guard means only stale rows are written).

Usage:
    python -m ops.scripts.recompute_exemplar_counts            # apply
    python -m ops.scripts.recompute_exemplar_counts --dry-run  # report only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.database import connect_one_shot  # noqa: E402

# Number of composites whose stored count does NOT match the real link count.
_PENDING_SQL = """
    SELECT COUNT(*) AS stale
    FROM composites c
    LEFT JOIN (
        SELECT q_number, COUNT(*) AS n
        FROM artifact_composites
        GROUP BY q_number
    ) ac ON ac.q_number = c.q_number
    WHERE c.exemplar_count IS DISTINCT FROM COALESCE(ac.n, 0)
"""

_RECOMPUTE_SQL = """
    UPDATE composites c
    SET exemplar_count = sub.n
    FROM (
        SELECT c2.q_number, COUNT(ac.p_number) AS n
        FROM composites c2
        LEFT JOIN artifact_composites ac ON ac.q_number = c2.q_number
        GROUP BY c2.q_number
    ) sub
    WHERE c.q_number = sub.q_number
      AND c.exemplar_count IS DISTINCT FROM sub.n
"""

# Spot-check witness from the issue: inflated before, real witness count = 3.
_SPOT_SQL = """
    SELECT c.q_number,
           c.exemplar_count AS stored,
           COUNT(ac.p_number) AS real_witnesses
    FROM composites c
    LEFT JOIN artifact_composites ac ON ac.q_number = c.q_number
    WHERE c.q_number = ANY(%s)
    GROUP BY c.q_number, c.exemplar_count
    ORDER BY c.q_number
"""

_SPOT_QS = ["Q000376"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many rows are stale and the spot-check, but do not write.",
    )
    args = ap.parse_args()

    conn = connect_one_shot()
    try:
        with conn.cursor() as cur:
            cur.execute(_PENDING_SQL)
            pending_row = cur.fetchone()
            pending = pending_row["stale"] if pending_row else 0
            print(f"composites with a stale exemplar_count: {pending}")

            cur.execute(_SPOT_SQL, (_SPOT_QS,))
            print("spot-check BEFORE:")
            for row in cur.fetchall():
                print(
                    f"  {row['q_number']}: stored={row['stored']} "
                    f"real_witnesses={row['real_witnesses']}"
                )

            if args.dry_run:
                print("dry-run: no changes written.")
                return 0

            cur.execute(_RECOMPUTE_SQL)
            updated = cur.rowcount or 0
            conn.commit()
            print(f"updated {updated} composite rows.")

            cur.execute(_SPOT_SQL, (_SPOT_QS,))
            print("spot-check AFTER:")
            for row in cur.fetchall():
                print(
                    f"  {row['q_number']}: stored={row['stored']} "
                    f"real_witnesses={row['real_witnesses']}"
                )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
