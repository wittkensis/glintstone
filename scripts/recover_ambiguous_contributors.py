"""Recover ambiguous-initial scholar credits (#262).

This script has TWO independent recovery passes, run in this order:

PASS 1 — PROSE FULL-NAME (added 2026-06-25, for the orphaned-no-roster case)
-----------------------------------------------------------------------------
``core.credits_parser.normalize_name`` deliberately reduces a credit name to a
``surname_<first-initial-only>`` form. That throws away a *second* initial: the
prose "J.N. Postgate" normalizes to ``postgate_j`` (one ``j``), which collides
with both ``postgate_jn`` (J. Nicholas Postgate, scholar 1048) and
``postgate_jp`` (J. P. Postgate, scholar 56894) — so the #261 backfill correctly
refused it. Likewise "Tyler Yoder" normalizes to ``yoder_t`` (one ``t``), which
matches no scholar key at all (the scholar is stored as ``yoder_tr``).

The fix does NOT relax accuracy. It re-reads the FULL prose name (keeping every
given initial AND every full given word) and attributes ONLY when that fuller
form is consistent with EXACTLY ONE scholar globally (same surname; each prose
given token a prefix-/initial-compatible match for the scholar's given token in
order; the prose must never carry MORE given tokens than the scholar). So:

  "J.N. Postgate"      -> given (j, n)        -> postgate_jn ONLY  (not _jp) -> attribute
  "Tyler Yoder"        -> given (word "tyler")-> yoder_tr ONLY              -> attribute
  "J. Postgate"        -> given (j)           -> postgate_jn AND _jp (2)    -> REFUSE
  "Nicholas Postgate"  -> given (word)        -> postgate_n ONLY            -> attribute

This pass needs NO roster: the disambiguation comes entirely from the fuller
prose form itself, matched against the global scholar list. A bare ambiguous
initial with no fuller form nearby ("J. Postgate" alone) still has 2 candidates
and is still refused. Accuracy over coverage (CLAUDE.md), unchanged.

PASS 2 — PER-PROJECT ROSTER (original #262 path)
------------------------------------------------

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
import re
import sys
import unicodedata
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


# --- PASS 1: prose full-name disambiguation ------------------------------
#
# These helpers re-read the FULL prose form a credit carries (every given
# initial AND every full given word, in order) rather than the lossy
# ``surname_<first-initial>`` form ``normalize_name`` produces. They are pure
# functions (no DB) so they are unit-tested directly in
# tests/test_recover_prose_fullname.py.

_NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}


def parse_person_tokens(raw: str) -> tuple[str, list[tuple[str, str]]] | None:
    """Parse a personal name into ``(surname, given_tokens)`` keeping detail.

    ``given_tokens`` is an ordered list of ``(kind, value)`` where ``kind`` is
    ``"init"`` (a single-initial token like "J." or "J") or ``"word"`` (a full
    given name like "Tyler"). A compound initial token like "J.N." is expanded
    into two ``("init", "j")`` and ``("init", "n")`` entries, mirroring how a
    scholar stored as ``postgate_jn`` carries two initials.

    Returns ``None`` when the input does not look like a two-token person name
    (no surname + at least one given token) — the caller treats that as no
    match. Folding/cleaning mirrors ``credits_parser.normalize_name`` so the two
    stay consistent (ASCII-fold, drop date and honorific-suffix tokens).
    """
    name = raw.strip()
    if not name:
        return None
    # "Surname, Given" -> "Given Surname" (same convention as normalize_name).
    if "," in name:
        surname_part, _, given_part = name.partition(",")
        name = f"{given_part.strip()} {surname_part.strip()}".strip()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.replace("‐", "-").replace("‑", "-")  # fancy hyphens

    tokens = [t for t in re.split(r"\s+", name) if t]
    cleaned: list[str] = []
    for tok in tokens:
        bare = re.sub(r"[^\w\-']", "", tok).lower()
        if not bare:
            continue
        if re.fullmatch(r"\d{3,4}(-\d{0,4})?", bare):  # date/lifespan token
            continue
        if bare in _NAME_SUFFIXES:
            continue
        cleaned.append(tok)
    if len(cleaned) < 2:
        return None

    surname = re.sub(r"[^\w\-]", "", cleaned[-1].lower(), flags=re.UNICODE).strip("_")
    if not surname or surname == "-":
        return None

    given: list[tuple[str, str]] = []
    for g in cleaned[:-1]:
        letters = re.findall(r"[A-Za-z]", g)
        if not letters:
            continue
        # "J.N." -> two initials; a bare "J" / "J." -> one initial; "Tyler" -> word.
        if "." in g and len(letters) > 1:
            for c in letters:
                given.append(("init", c.lower()))
        elif len(g.rstrip(".")) == 1:
            given.append(("init", letters[0].lower()))
        else:
            given.append(("word", "".join(c.lower() for c in letters)))
    if not given:
        return None
    return surname, given


def full_name_consistent(
    credit_given: list[tuple[str, str]],
    scholar_given: list[tuple[str, str]],
) -> bool:
    """True if a credit's given tokens uniquely fit a scholar's, position by pos.

    Conservative, never a fuzzy match:
      - The credit must not carry MORE given tokens than the scholar (a credit
        with extra information we cannot confirm is refused).
      - At each position the first letters must match.
      - Two full words must be equal ("Tyler" only fits "Tyler", not "Tobias").
      - A credit *word* against a scholar *initial* is refused: the credit claims
        more than the scholar record proves, so we cannot confirm identity.
      - A credit *initial* against a scholar *word* is fine (the initial is a
        prefix of the word) — that is exactly the "J.N." -> "John Nicholas" case.
    """
    if not credit_given or len(credit_given) > len(scholar_given):
        return False
    for (c_kind, c_val), (s_kind, s_val) in zip(credit_given, scholar_given):
        if not c_val or not s_val or c_val[0] != s_val[0]:
            return False
        if c_kind == "word" and s_kind == "word" and c_val != s_val:
            return False
        if c_kind == "word" and s_kind == "init":
            return False
    return True


def _scholars_full_by_surname(
    conn: psycopg.Connection,
) -> dict[str, list[tuple[int, list[tuple[str, str]]]]]:
    """surname -> list of (scholar_id, parsed given-tokens) over ALL scholars.

    Built from ``scholars.name`` (the human display form, e.g. "Tyler R. Yoder",
    "Postgate, John Nicholas") so the full given names/initials are available for
    the prose full-name match — ``normalized_name`` alone has lost them.
    """
    rows = conn.execute(
        "SELECT id, name FROM scholars WHERE name IS NOT NULL AND name <> ''"
    ).fetchall()
    by_surname: dict[str, list[tuple[int, list[tuple[str, str]]]]] = defaultdict(list)
    for r in rows:
        parsed = parse_person_tokens(r["name"])
        if parsed is None:
            continue
        surname, given = parsed
        by_surname[surname].append((r["id"], given))
    return by_surname


def recover(project: str | None = None, dry_run: bool = False, sample: int = 40) -> int:
    with psycopg.connect(_conninfo(), row_factory=dict_row) as conn:
        unique = _unique_index(conn)
        by_surname = _scholars_by_surname(conn)
        full_by_surname = _scholars_full_by_surname(conn)
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
        recovered_by_form: Counter = Counter()  # Pass 2 (roster)
        prose_by_form: Counter = Counter()  # Pass 1 (prose full-name)
        prose_evidence: dict[str, tuple[int, str]] = {}  # nn -> (scholar_id, raw)
        refused_no_roster: Counter = Counter()
        refused_multi: Counter = Counter()
        not_ambiguous_skipped = 0
        samples_shown = 0
        prose_samples_shown = 0

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

                # --- PASS 1: prose full-name (no roster needed). Re-read the
                # FULL prose form and attribute only on a GLOBALLY unique match.
                parsed = parse_person_tokens(m.name)
                if parsed is not None and parsed[0] == surname:
                    _, credit_given = parsed
                    prose_cands = sorted(
                        {
                            sid
                            for (sid, sch_given) in full_by_surname.get(surname, [])
                            if full_name_consistent(credit_given, sch_given)
                        }
                    )
                    if len(prose_cands) == 1:
                        sid = prose_cands[0]
                        recovered.append(
                            (c["p_number"], sid, m.role, proj, c["id"], m.name)
                        )
                        prose_by_form[nn] += 1
                        prose_evidence[nn] = (sid, m.name.strip())
                        if dry_run and prose_samples_shown < sample:
                            print(
                                f"  PROSE   {c['p_number']} {m.role:11s} "
                                f"{m.name!r} -> {nn} (scholar {sid}, "
                                f"globally-unique full-name, project {proj})"
                            )
                            prose_samples_shown += 1
                        continue
                    # 0 or >=2 global candidates -> not confidently recoverable
                    # by prose alone; fall through to the roster pass below.

                # --- PASS 2: per-project roster.
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
            f"  RECOVERED via PROSE full-name (global-unique): "
            f"{sum(prose_by_form.values()):,} pairs "
            f"({len(prose_by_form):,} distinct names)"
        )
        for nn, n in prose_by_form.most_common(15):
            sid, raw = prose_evidence.get(nn, (0, "?"))
            print(f"     +{n:4d}  {nn:14s} <- prose {raw!r} -> scholar {sid}")
        print(
            f"  RECOVERED via project ROSTER match          : "
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
