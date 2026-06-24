"""Recover ambiguous-initial scholar credits via per-project rosters (#262).

The #261 backfill (scripts/backfill_artifact_contributors.py) attributes a parsed
credit name ONLY when its ``surname_initials`` form is globally unique among
``scholars.normalized_name``. That left ~794 credit pairs unattributed — almost
all ambiguous initials such as ``postgate_j`` (412) and ``yoder_t`` (379): the
prose carried only an initial ("J. Postgate"), whose normalized form collides
with, or is a prefix of, more than one scholar (``postgate_j`` vs the fuller
``postgate_jn``), so the global-uniqueness gate (correctly) declined to guess.

This script recovers those credits WITHOUT relaxing accuracy, by disambiguating
each ambiguous initial against the **roster of the same ORACC project**:

  A scholar is "on a project's roster" if they ALREADY have at least one
  confident (globally-unique-name) attribution in artifact_contributors for that
  oracc_project — i.e. the #261 backfill already placed them there from a full
  name elsewhere in the same project.

For an unmatched ambiguous form ``surname_<inits>`` appearing in project P, the
candidate set is the project-P roster scholars whose normalized_name is
consistent with that initial: it equals ``surname_<inits>`` exactly, or it is
``surname_<inits...>`` where the credit's initials are a leading prefix of the
scholar's initials (so ``postgate_j`` is consistent with ``postgate_jn`` but NOT
with ``postgate_a``). The surname must match exactly.

Attribution rule (accuracy over coverage — CLAUDE.md):
  - Attribute ONLY when EXACTLY ONE roster scholar in that project is consistent
    with the initial. One project credibly names one specific Postgate.
  - Zero consistent roster scholars  -> leave unattributed (no roster evidence).
  - Two or more consistent roster scholars -> leave unattributed (genuinely
    ambiguous even within the project; refuse to guess).
  - The surname is matched exactly and the initial must be a prefix of the
    roster scholar's initials — never a fuzzy/edit-distance match.

Idempotent + fill-only: writes are ``INSERT ... ON CONFLICT DO NOTHING`` against
the same unique key the backfill uses, with role/project/source-credit provenance
preserved, exactly like #261. Re-running never duplicates.

Usage:
  # Always dry-run first — shows every recovered + every refused-ambiguous pair:
  python -m scripts.recover_ambiguous_contributors --dry-run

  # One project at a time (recommended for review):
  python -m scripts.recover_ambiguous_contributors --project rinap --dry-run

  # Commit the recovered links (idempotent, fill-only):
  python -m scripts.recover_ambiguous_contributors
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
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


def _split_form(nn: str) -> tuple[str, str]:
    """Split a normalized_name 'surname_initials' into (surname, initials).

    A stored disambiguation digit suffix (radner_k1) is stripped from the
    initials so it does not break the prefix comparison; the surname is the part
    before the LAST underscore so hyphen/underscore surnames stay intact.
    """
    surname, _, inits = nn.rpartition("_")
    if not surname:  # no underscore -> not a surname_initials form
        return nn, ""
    inits = inits.rstrip("0123456789")
    return surname, inits


def _unique_index(conn: psycopg.Connection) -> set[str]:
    """Set of globally-unique normalized_name keys (the #261 attributable set).

    A name in this set was already handled by the backfill; we only try to
    recover names that are NOT here (the ambiguous remainder).
    """
    rows = conn.execute(
        "SELECT normalized_name FROM scholars "
        "WHERE normalized_name IS NOT NULL AND normalized_name <> ''"
    ).fetchall()
    counts: Counter[str] = Counter(r["normalized_name"] for r in rows)
    return {nn for nn, c in counts.items() if c == 1}


def _scholars_by_surname(
    conn: psycopg.Connection,
) -> dict[str, list[tuple[int, str]]]:
    """surname -> list of (scholar_id, initials) over ALL scholars.

    Used to find the candidate people who share an ambiguous surname; the
    per-project roster then narrows them to one (or refuses).
    """
    rows = conn.execute(
        "SELECT id, normalized_name FROM scholars "
        "WHERE normalized_name IS NOT NULL AND normalized_name <> ''"
    ).fetchall()
    by_surname: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for r in rows:
        surname, inits = _split_form(r["normalized_name"])
        if surname:
            by_surname[surname].append((r["id"], inits))
    return by_surname


def _project_rosters(conn: psycopg.Connection) -> dict[str, set[int]]:
    """oracc_project -> set of scholar_ids already confidently attributed there.

    This is the per-project author roster the disambiguation leans on. It comes
    straight from the #261 backfill's output, so it only contains scholars whose
    FULL name matched a globally-unique key in that project — high-confidence
    seed evidence, never another guess.
    """
    rows = conn.execute(
        "SELECT DISTINCT oracc_project, scholar_id FROM artifact_contributors"
    ).fetchall()
    rosters: dict[str, set[int]] = defaultdict(set)
    for r in rows:
        rosters[r["oracc_project"]].add(r["scholar_id"])
    return rosters


def _initial_consistent(credit_inits: str, scholar_inits: str) -> bool:
    """True if the credit's initials are a leading prefix of the scholar's.

    'j' is consistent with 'jn' (J. Postgate vs J.N. Postgate); 'jn' is
    consistent with 'jn'; 'j' is NOT consistent with 'a'. An empty credit
    initial is rejected (we require at least one initial to disambiguate).
    """
    if not credit_inits:
        return False
    return scholar_inits.startswith(credit_inits)


def recover(project: str | None = None, dry_run: bool = False, sample: int = 40) -> int:
    with psycopg.connect(_conninfo(), row_factory=dict_row) as conn:
        unique = _unique_index(conn)
        by_surname = _scholars_by_surname(conn)
        rosters = _project_rosters(conn)
        print(
            f"Scholars: {sum(len(v) for v in by_surname.values()):,} | "
            f"unique keys: {len(unique):,} | "
            f"projects with a roster: {len(rosters):,}"
        )

        sql = "SELECT id, p_number, oracc_project, credits_text FROM artifact_credits"
        params: list = []
        if project:
            sql += " WHERE oracc_project = %s"
            params.append(project)
        credits = conn.execute(sql, tuple(params)).fetchall()
        print(f"Credit rows to scan: {len(credits):,}")

        recovered: list[tuple] = []  # rows to insert
        recovered_by_form: Counter = Counter()
        refused_no_roster: Counter = Counter()
        refused_multi: Counter = Counter()
        not_ambiguous_skipped = 0
        samples_shown = 0

        for c in credits:
            proj = c["oracc_project"]
            roster = rosters.get(proj, set())
            for m in parse_credits(c["credits_text"]):
                nn = normalize_name(m.name)
                if not nn or nn in unique:
                    # Empty (not a person) or already attributable by #261.
                    not_ambiguous_skipped += 1
                    continue

                surname, inits = _split_form(nn)
                if not surname or not inits:
                    refused_no_roster[nn] += 1
                    continue

                # Candidate people sharing this surname, narrowed to (a) this
                # project's roster and (b) initial-consistency.
                candidates = [
                    sid
                    for (sid, sch_inits) in by_surname.get(surname, [])
                    if sid in roster and _initial_consistent(inits, sch_inits)
                ]
                # Deduplicate scholar ids (a scholar may appear once per row form).
                candidates = sorted(set(candidates))

                if len(candidates) == 1:
                    sid = candidates[0]
                    recovered.append(
                        (c["p_number"], sid, m.role, proj, c["id"], m.name)
                    )
                    recovered_by_form[nn] += 1
                    if dry_run and samples_shown < sample:
                        print(
                            f"  RECOVER {c['p_number']} {m.role:11s} "
                            f"{m.name!r} -> {nn} (scholar {sid}, project {proj})"
                        )
                        samples_shown += 1
                elif len(candidates) == 0:
                    refused_no_roster[nn] += 1
                else:
                    # Two+ roster scholars consistent with the initial — genuinely
                    # ambiguous even within the project. Refuse.
                    refused_multi[nn] += 1

        print("\n=== recovery report (#262) ===")
        print(
            f"  already-attributable / non-person (skipped): {not_ambiguous_skipped:,}"
        )
        print(
            f"  RECOVERED (unique project-roster match)     : "
            f"{sum(recovered_by_form.values()):,} pairs "
            f"({len(recovered_by_form):,} distinct names)"
        )
        for nn, n in recovered_by_form.most_common(15):
            print(f"     +{n:4d}  {nn}")
        print(
            f"  refused — no roster evidence                : "
            f"{sum(refused_no_roster.values()):,} "
            f"({len(refused_no_roster):,} distinct)"
        )
        print(
            f"  refused — ambiguous within project (>=2)    : "
            f"{sum(refused_multi.values()):,} "
            f"({len(refused_multi):,} distinct)"
        )
        if refused_multi:
            print("  top refused-ambiguous (left UNATTRIBUTED, by policy):")
            for nn, n in refused_multi.most_common(10):
                print(f"     {n:5d}  {nn}")

        if dry_run:
            print(f"\nDRY RUN — {len(recovered):,} recovered links NOT written.")
            return 0

        if not recovered:
            print("\nNo links to recover.")
            return 0

        inserted = 0
        with conn.cursor() as cur:
            for start in range(0, len(recovered), 1000):
                batch = recovered[start : start + 1000]
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
        print(f"\nInserted (new) recovered links: {inserted:,}")
        print(f"artifact_contributors total now: {total_now:,}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", help="limit to one oracc_project (e.g. rinap)")
    ap.add_argument(
        "--dry-run", action="store_true", help="report recoveries, write nothing"
    )
    ap.add_argument("--sample", type=int, default=40, help="dry-run sample size")
    args = ap.parse_args()
    return recover(project=args.project, dry_run=args.dry_run, sample=args.sample)


if __name__ == "__main__":
    sys.exit(main())
