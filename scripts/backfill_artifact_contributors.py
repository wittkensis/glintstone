"""Backfill artifact_contributors from artifact_credits prose (#261).

Parses each ``artifact_credits`` row into (name, role) pairs, matches each name
**conservatively** against ``scholars.normalized_name`` (exact, globally-unique
key), and inserts one ``artifact_contributors`` row per artifact x scholar x
role. Idempotent (``ON CONFLICT DO NOTHING``), fill-only, non-destructive.

CONSERVATIVE MATCHING (scholars' careers depend on accurate attribution —
CLAUDE.md): a parsed name is attributed ONLY when its normalized form matches
exactly one scholar. ``scholars.normalized_name`` is globally unique (verified:
0 duplicate keys over 86,504 rows), so an exact match is unambiguous. A name
with no normalized form, or no matching scholar, is LEFT UNATTRIBUTED and
counted in the unmatched tally — never guessed.

Run on the deploy server (the prod DB lives on the VPS). Locally it runs against
the local Postgres via the same .env config.

Usage:
  # Subset verify first — report matches for one project (no writes):
  python -m scripts.backfill_artifact_contributors --project saao --dry-run

  # Subset verify a single scholar's credits (no writes):
  python -m scripts.backfill_artifact_contributors --scholar 792 --dry-run

  # Full backfill (idempotent, fill-only):
  python -m scripts.backfill_artifact_contributors
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import get_settings  # noqa: E402
from core.credits_parser import normalize_name, parse_credits  # noqa: E402


def _conninfo() -> str:
    s = get_settings()
    return s.database_url or s.psycopg_conninfo()


def _load_scholar_index(conn: psycopg.Connection) -> dict[str, int]:
    """normalized_name -> scholar id. Only unique keys are kept; a normalized
    name shared by >1 scholar is excluded so it can never produce a match.
    """
    rows = conn.execute(
        "SELECT normalized_name, id FROM scholars "
        "WHERE normalized_name IS NOT NULL AND normalized_name <> ''"
    ).fetchall()
    counts: Counter[str] = Counter(r["normalized_name"] for r in rows)
    index: dict[str, int] = {}
    for r in rows:
        nn = r["normalized_name"]
        if counts[nn] == 1:
            index[nn] = r["id"]
    dropped = sum(1 for n, c in counts.items() if c > 1)
    if dropped:
        print(f"  note: {dropped} non-unique normalized_name key(s) excluded")
    return index


def backfill(
    project: str | None = None,
    scholar_id: int | None = None,
    dry_run: bool = False,
    sample: int = 25,
) -> int:
    with psycopg.connect(_conninfo(), row_factory=dict_row) as conn:
        index = _load_scholar_index(conn)
        print(f"Scholar index: {len(index):,} unique normalized names")

        where = []
        params: list = []
        if project:
            where.append("oracc_project = %s")
            params.append(project)
        # --scholar filters credits to those whose prose contains a name that
        # normalizes to this scholar's normalized_name (verify mode only).
        target_nn: str | None = None
        if scholar_id is not None:
            row = conn.execute(
                "SELECT normalized_name FROM scholars WHERE id = %s", (scholar_id,)
            ).fetchone()
            if not row or not row["normalized_name"]:
                print(f"Scholar {scholar_id} has no normalized_name; nothing to do.")
                return 1
            target_nn = row["normalized_name"]

        sql = "SELECT id, p_number, oracc_project, credits_text FROM artifact_credits"
        if where:
            sql += " WHERE " + " AND ".join(where)

        credits = conn.execute(sql, tuple(params)).fetchall()
        print(f"Credits rows to parse: {len(credits):,}")

        # Tallies.
        pairs_total = 0  # (name, role) pairs extracted
        matched = 0  # pairs that matched a unique scholar
        unmatched = Counter()  # normalized form -> count of misses
        unnormalizable = 0  # names that produced no normalized form
        links: list[tuple] = []  # rows to insert
        per_scholar = Counter()  # scholar_id -> distinct artifacts (for report)
        samples_shown = 0

        for c in credits:
            matches = parse_credits(c["credits_text"])
            for m in matches:
                pairs_total += 1
                nn = normalize_name(m.name)
                if not nn:
                    unnormalizable += 1
                    continue
                sid = index.get(nn)
                if sid is None:
                    unmatched[nn] += 1
                    continue
                if target_nn is not None and nn != target_nn:
                    # Verify-by-scholar mode: only collect this scholar's links,
                    # but still count global matches for the rate.
                    matched += 1
                    continue
                matched += 1
                per_scholar[sid] += 1
                links.append(
                    (
                        c["p_number"],
                        sid,
                        m.role,
                        c["oracc_project"],
                        c["id"],
                        m.name,
                    )
                )
                if dry_run and samples_shown < sample:
                    print(
                        f"  MATCH {c['p_number']} {m.role:11s} "
                        f"{m.name!r} -> {nn} (scholar {sid})"
                    )
                    samples_shown += 1

        rate = (matched / pairs_total * 100) if pairs_total else 0.0
        print("\n=== parse / match report ===")
        print(f"  credit pairs extracted : {pairs_total:,}")
        print(f"  matched (unique scholar): {matched:,}  ({rate:.1f}%)")
        print(f"  unnormalizable names   : {unnormalizable:,}")
        print(
            f"  unmatched normal forms : {sum(unmatched.values()):,} "
            f"({len(unmatched):,} distinct)"
        )
        if unmatched:
            print("  top unmatched (left UNATTRIBUTED, by policy):")
            for nn, n in unmatched.most_common(15):
                print(f"     {n:5d}  {nn}")

        if target_nn is not None:
            n_links = len(links)
            n_arts = len({lnk[0] for lnk in links})
            print(
                f"\n  scholar {scholar_id} ({target_nn}): "
                f"{n_links:,} role-links over {n_arts:,} distinct artifacts"
            )

        if per_scholar:
            print("\n  top scholars by distinct contributions (this run):")
            top = sorted(per_scholar.items(), key=lambda kv: -kv[1])[:10]
            for sid, n in top:
                nm = conn.execute(
                    "SELECT name FROM scholars WHERE id = %s", (sid,)
                ).fetchone()
                print(f"     scholar {sid:>6} {nm['name']!r:34s}  {n:,} links")

        if dry_run:
            print(f"\nDRY RUN — {len(links):,} links NOT written.")
            return 0

        if not links:
            print("\nNo links to insert.")
            return 0

        inserted = 0
        with conn.cursor() as cur:
            for batch_start in range(0, len(links), 1000):
                batch = links[batch_start : batch_start + 1000]
                cur.executemany(
                    """
                    INSERT INTO artifact_contributors
                        (p_number, scholar_id, role, oracc_project,
                         source_credit_id, matched_name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (p_number, scholar_id, role, oracc_project)
                    DO NOTHING
                    """,
                    batch,
                )
                inserted += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        conn.commit()
        total_now = conn.execute(
            "SELECT COUNT(*) AS n FROM artifact_contributors"
        ).fetchone()["n"]
        print(f"\nInserted (new) links: {inserted:,}")
        print(f"artifact_contributors total now: {total_now:,}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", help="limit to one oracc_project (e.g. saao)")
    ap.add_argument(
        "--scholar", type=int, help="verify one scholar's matches (report-only)"
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="parse + report, write nothing"
    )
    ap.add_argument("--sample", type=int, default=25, help="dry-run sample size")
    args = ap.parse_args()
    return backfill(
        project=args.project,
        scholar_id=args.scholar,
        dry_run=args.dry_run,
        sample=args.sample,
    )


if __name__ == "__main__":
    sys.exit(main())
