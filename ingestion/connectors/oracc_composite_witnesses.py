"""ORACC composite-witness linkage connector (issue #293).

Backfills the `artifact_composites` table (composite Q-number -> witness/exemplar
P-number links) for composites that the ATF parser never linked.

Why this is needed
------------------
Today the only source of composite->exemplar links is the `>>Q...` reference
lines inside `cdliatf_unblocked.atf`, parsed by `atf-parser`. That file covers
only ~659 of our 8,766 composites. The other thousands carry an ORACC
`exemplar_count` but have ZERO linked witnesses, so their composition detail page
cannot pick a representative exemplar and cannot show any transliteration (ATF).

The witness mapping, however, IS present in the ORACC project `catalogue.json`
files we already hold on disk. Each composite member entry (a `Q`-keyed record)
carries a `cdli_id_numbers` field: a semicolon-delimited list of the CDLI
P-numbers that are the physical witnesses (exemplars) of that composition, e.g.

    Q000376 "Utu-hegal 4"
        exemplar_info:    "AO 06018; AO 06314; Ist Ni 04167"
        cdli_id_numbers:  "P227538; P227539; P227540"

`cdli_id_numbers` is the authoritative, ORACC-curated witness list. The parallel
`exemplar_info` field gives the human-readable museum numbers for the same
witnesses, in the same order — a cross-check that these P-numbers really are the
exemplars and not some unrelated identifiers.

Accuracy over coverage
----------------------
- Only `cdli_id_numbers` is read. We do NOT infer witnesses from prose, museum
  numbers, or any heuristic. A composite whose catalogue entry has no
  `cdli_id_numbers` is left unlinked (counted in `skipped_no_mapping`) rather
  than guessed — a wrong composite->exemplar link is bad scholarly data.
- `cdli_composite_id` / `id_composite` (the composite's OWN P-number, when a
  composite is itself catalogued as an artifact) is NEVER treated as a witness.
  We only parse the `cdli_id_numbers` value, so that field is never conflated in.
- A link is only written when BOTH the Q-number exists in `composites` AND the
  witness P-number exists in `artifacts` (the `artifact_composites` foreign keys
  require both). Pairs failing either guard are routed to a skip count, not
  forced in.

Idempotency
-----------
- Link insert is `ON CONFLICT (p_number, q_number) DO NOTHING` — re-running never
  duplicates and never disturbs `atf-parser`-sourced links.
- `composites.exemplar_count` is then RECOMPUTED as the true `COUNT(*)` of linked
  witnesses for every touched Q-number, so the displayed exemplar count stays
  consistent with the link rows whether this runs once or many times. (It does
  not blindly increment, which would drift on re-run.)

Runs after: cdli-catalog and oracc-catalog (so witness P-numbers exist in
`artifacts`) and atf-parser (so existing links/exemplar_counts are present and we
only fill genuine gaps).
"""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

ORACC_BASE = Path("source-data/sources/ORACC")

# A CDLI P-number is exactly "P" followed by digits. ORACC zero-pads to 6
# digits; we match P + 5-or-more digits to be tolerant and normalise below.
_PNUM = re.compile(r"\bP\d{5,}\b")

BATCH_SIZE = 1000


def _iter_catalogues(base: Path) -> Iterator[Path]:
    pattern = str(base / "**" / "catalogue.json")
    for path_str in glob.glob(pattern, recursive=True):
        yield Path(path_str)


def _norm_p(p: str) -> str:
    """Normalise a P-number to canonical zero-padded 6-digit form (P000000).

    CDLI P-numbers are 6 digits. We strip any leading zeros first (so a stray
    over-padded form like "P00256242" collapses to its canonical value) then
    re-pad to a minimum of 6, leaving genuine >6-digit numbers untouched.
    """
    digits = p[1:].lstrip("0") or "0"
    return "P" + digits.zfill(6)


class OraccCompositeWitnessesConnector(SourceConnector):
    id = "oracc-composite-witnesses"
    display_name = "ORACC Composite Witnesses"
    description = (
        "Backfills composite->exemplar links (artifact_composites) from the "
        "ORACC catalogue.json `cdli_id_numbers` witness lists, so composites "
        "that the ATF parser never linked can surface a representative "
        "exemplar's transliteration (#293)."
    )
    kind = "derived"
    runs_after = ["cdli-catalog", "oracc-catalog", "atf-parser"]
    upstream_url = "https://oracc.museum.upenn.edu/"
    license = "CC-BY-SA-3.0"
    license_url = "https://creativecommons.org/licenses/by-sa/3.0/"
    citation = (
        "Open Richly Annotated Cuneiform Corpus (ORACC), "
        "https://oracc.museum.upenn.edu/ — project catalogue.json "
        "`cdli_id_numbers` witness lists."
    )

    def __init__(self, base: Path | None = None) -> None:
        self.base = Path(base) if base else ORACC_BASE

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Yield one record per (q_number, witness p_number) high-confidence pair.

        First-seen pair wins; duplicates across projects are de-duplicated here
        so the loader does less work. Only `cdli_id_numbers` is parsed.
        """
        catalogues = list(_iter_catalogues(self.base))
        ctx.info(
            "oracc_composite_witnesses.scan_start",
            catalogue_count=len(catalogues),
        )

        pairs: set[tuple[str, str]] = set()
        q_with_mapping: set[str] = set()
        q_without_mapping: set[str] = set()

        for cat_path in catalogues:
            try:
                with open(cat_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, ValueError, OSError):
                ctx.warn("oracc_composite_witnesses.bad_json", path=str(cat_path))
                continue

            for key, entry in data.get("members", {}).items():
                if not key.startswith("Q") or not isinstance(entry, dict):
                    continue
                raw = entry.get("cdli_id_numbers")
                if not raw:
                    q_without_mapping.add(key)
                    continue
                # Parse ONLY the cdli_id_numbers value. cdli_composite_id (the
                # composite's own artifact P-number) lives in a different key and
                # is never read here, so it cannot be mistaken for a witness.
                ps = _PNUM.findall(str(raw))
                if not ps:
                    q_without_mapping.add(key)
                    continue
                q_with_mapping.add(key)
                for p in ps:
                    pairs.add((_norm_p(p), key))

        # A Q that has a mapping in one project but not another is still mapped.
        q_without_mapping -= q_with_mapping

        ctx.info(
            "oracc_composite_witnesses.parsed",
            distinct_pairs=len(pairs),
            q_with_mapping=len(q_with_mapping),
            q_without_mapping=len(q_without_mapping),
        )

        for p, q in pairs:
            yield {"p_number": p, "q_number": q}

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        # Guard sets: a link's FKs require the Q in composites and the P in
        # artifacts. Load both once so we can route un-resolvable pairs to a skip
        # count instead of letting the INSERT raise.
        known_q: set[str] = {
            (r[0] if isinstance(r, tuple) else r["q_number"])
            for r in ctx.db.execute("SELECT q_number FROM composites").fetchall()
        }
        known_p: set[str] = {
            (r[0] if isinstance(r, tuple) else r["p_number"])
            for r in ctx.db.execute("SELECT p_number FROM artifacts").fetchall()
        }
        ctx.info(
            "oracc_composite_witnesses.guards",
            composites=len(known_q),
            artifacts=len(known_p),
        )

        stats = LoadStats()
        touched_q: set[str] = set()
        considered = 0
        skipped_no_composite = 0
        skipped_no_artifact = 0
        batch: list[tuple[str, str]] = []

        def _flush(cur) -> None:
            if not batch:
                return
            cur.executemany(
                "INSERT INTO artifact_composites (p_number, q_number) "
                "VALUES (%s, %s) ON CONFLICT (p_number, q_number) DO NOTHING",
                batch,
            )
            batch.clear()

        with ctx.db.cursor() as cur:
            for row in rows:
                considered += 1
                p = row["p_number"]
                q = row["q_number"]
                if q not in known_q:
                    # Witness list references a composite we don't hold — skip,
                    # don't fabricate the composite.
                    skipped_no_composite += 1
                    continue
                if p not in known_p:
                    # Witness tablet not in our catalog (no corpusjson / not in
                    # CDLI) — would violate the FK and could never show ATF. Skip.
                    skipped_no_artifact += 1
                    continue
                batch.append((p, q))
                touched_q.add(q)
                if len(batch) >= BATCH_SIZE:
                    _flush(cur)
                    ctx.db.commit()

            _flush(cur)
            ctx.db.commit()

            # Recompute exemplar_count from the authoritative link rows for ALL
            # composites — not just the Q's this run touched (#309). The earlier
            # touched-only recompute could leave a composite's count stale whenever
            # its link set changed via another path (e.g. the atf-parser, a manual
            # fix, or a witness P-number that only later appeared in `artifacts`):
            # those Q's are never in `touched_q`, so their count silently drifted —
            # exactly the recurrence #295 guarded against. A single global pass
            # makes exemplar_count self-heal on every run.
            #
            # Set it to the true COUNT(*) of links per Q, and explicitly to 0 for
            # composites that have no links at all (a LEFT JOIN, so a composite that
            # lost all its witnesses correctly drops to 0 rather than keeping a
            # phantom count). `IS DISTINCT FROM` keeps it a no-op write when already
            # correct, so the statement is idempotent and cheap on a clean re-run.
            cur.execute(
                """
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
            )
            updated_counts = cur.rowcount or 0
            ctx.db.commit()

        # Honest inserted count: links present now that resolved from this source.
        stats.skipped = skipped_no_composite + skipped_no_artifact
        ctx.info(
            "oracc_composite_witnesses.done",
            considered=considered,
            linkable_pairs=considered - stats.skipped,
            skipped_no_composite=skipped_no_composite,
            skipped_no_artifact=skipped_no_artifact,
            touched_composites=len(touched_q),
            exemplar_counts_updated=updated_counts,
        )
        stats.inserted = considered - stats.skipped
        return stats

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            """
            SELECT
                (SELECT COUNT(DISTINCT q_number) FROM artifact_composites) AS linked_q,
                (SELECT COUNT(DISTINCT ac.q_number)
                   FROM artifact_composites ac
                   JOIN text_lines tl ON tl.p_number = ac.p_number) AS atf_q
            """
        ).fetchone()
        linked_q = row[0] if isinstance(row, tuple) else row["linked_q"]
        atf_q = row[1] if isinstance(row, tuple) else row["atf_q"]
        ctx.info(
            "oracc_composite_witnesses.verify",
            composites_with_links=linked_q,
            composites_surfacing_atf=atf_q,
        )
        if linked_q < 659:
            raise AssertionError(
                f"Regression: composites with links dropped to {linked_q} "
                "(expected >= 659, the atf-parser baseline)"
            )
