"""ORACC artifact catalog connector (Fix C, issue #238).

The `oracc-atf` connector (Fix A, #273) only writes text_lines/tokens for
tablets that already have a row in `artifacts`. ~6,204 tablets have ORACC
corpusjson on disk — and are referenced by millions of open `no_line_match`
dead-letters from `oracc-lemmatizations` — but were never cataloged by the
CDLI catalog (they are ORACC-only P-numbers). Because they are not in
`artifacts`, oracc-atf silently skips them and their lemmas stay dead-lettered.

This connector closes that gap on the *catalog* side: it walks every ORACC
project `catalogue.json`, builds one merged metadata record per ORACC-only
P-number, and inserts a minimal-but-correct `artifacts` row for each tablet
that (a) is not already in `artifacts` and (b) has corpusjson on disk (so the
follow-up oracc-atf run can actually parse lines for it). With those rows in
place, re-running oracc-atf populates text_lines/tokens, and a dlq-replay of
oracc-lemmatizations resolves the now-matchable dead-letters.

Accuracy over coverage
----------------------
Only real catalogue fields are written. ORACC catalogues use inconsistent key
casing across projects (e.g. `genre` vs `Genre`, `museum_no` vs `Mus_no`); we
read a small, explicit alias list per target column and take the first non-null
value. Genuinely-absent fields are left NULL — nothing is fabricated. A P-number
with corpusjson but no catalogue entry (~10 tablets) still gets a minimal row
carrying only p_number + oracc_projects + db_source='oracc', which is enough to
unblock oracc-atf without inventing metadata.

Provenance: db_source is set to 'oracc' so these rows are distinguishable from
CDLI-sourced catalog rows; oracc_projects is a JSON array of the project(s) the
tablet appears in (same convention as oracc-enrichment).

Idempotency: the insert is `ON CONFLICT (p_number) DO NOTHING`, so re-running
never overwrites an existing artifact (CDLI- or ORACC-sourced) and never
duplicates. It only fills the genuinely-missing rows.

Runs after: cdli-catalog (so CDLI artifacts already exist and are not re-created
here) and annotation-runs. Must run BEFORE oracc-atf so the artifacts guard in
oracc-atf finally sees these P-numbers.
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

ORACC_BASE = Path("source-data/sources/ORACC")

# Per-target-column source-key aliases, in priority order. ORACC projects use
# inconsistent casing/keys; the lowercase canonical name is preferred, then
# known capitalized / project-specific variants. First non-empty value wins.
FIELD_ALIASES: dict[str, list[str]] = {
    "designation": ["designation"],
    "period": ["period", "Period_culture"],
    "provenience": ["provenience", "PROV_site"],
    "genre": ["genre", "Genre", "genres"],
    "subgenre": ["subgenre", "Subgenre"],
    "supergenre": ["supergenre"],
    "language": ["language", "Language", "langs"],
    "museum_no": ["museum_no", "Mus_no", "museum_number", "mus_no"],
    "excavation_no": ["excavation_no", "cdli_excavation_no"],
    "primary_publication": ["primary_publication"],
    "collection": ["collection", "collections"],
    "object_type": ["object_type", "OBJ_type", "artifact_type"],
    "material": ["material", "materials"],
}

# Columns written, in a stable order, for the INSERT statement.
ARTIFACT_COLUMNS = [
    "p_number",
    "designation",
    "period",
    "provenience",
    "genre",
    "subgenre",
    "supergenre",
    "language",
    "museum_no",
    "excavation_no",
    "primary_publication",
    "collection",
    "object_type",
    "material",
    "oracc_projects",
    "db_source",
]

BATCH_SIZE = 500


def _clean(val: object) -> str | None:
    """Normalize a catalogue value to a trimmed string or None.

    Lists (some projects store genres/languages as arrays) are joined with a
    comma; empty / falsey values become None so we never write empty strings.
    """
    if val is None:
        return None
    if isinstance(val, list):
        parts = [str(v).strip() for v in val if v is not None and str(v).strip()]
        val = ", ".join(parts)
    s = str(val).strip()
    return s or None


# A museum number is a placeholder when, after removing a collection prefix
# (letters) and dashes/em-dashes/spaces, no actual identifier remains — e.g.
# "BM —", "IM —", "-". ORACC uses these to mean "no museum number assigned";
# storing them would be misleading, so we treat them as absent.
def _is_placeholder_museum_no(s: str) -> bool:
    residue = s
    for ch in ("—", "–", "-", " ", ".", "?"):
        residue = residue.replace(ch, "")
    # strip a leading alphabetic collection prefix (BM, IM, NMSA, ...)
    residue = residue.lstrip("".join(c for c in residue if c.isalpha()))
    return residue == ""


def _pick(
    entry: dict, aliases: list[str], *, drop_placeholder_museum: bool = False
) -> str | None:
    for key in aliases:
        v = _clean(entry.get(key))
        if v is not None:
            if drop_placeholder_museum and _is_placeholder_museum_no(v):
                continue
            return v
    return None


def _iter_catalogues(base: Path) -> Iterator[Path]:
    pattern = str(base / "**" / "catalogue.json")
    for path_str in glob.glob(pattern, recursive=True):
        yield Path(path_str)


def _corpusjson_p_numbers(base: Path) -> set[str]:
    """Every P-number that has a corpusjson file on disk (parseable by oracc-atf)."""
    found: set[str] = set()
    pattern = str(base / "**" / "corpusjson" / "P*.json")
    for path_str in glob.glob(pattern, recursive=True):
        found.add(os.path.splitext(os.path.basename(path_str))[0])
    return found


class OraccCatalogConnector(SourceConnector):
    id = "oracc-catalog"
    display_name = "ORACC Artifact Catalog"
    description = (
        "Creates artifacts rows for ORACC-only tablets (corpusjson on disk but "
        "absent from the CDLI catalog) from ORACC catalogue.json, so oracc-atf "
        "can parse their lines and dead-letters can be resolved (Fix C, #238)."
    )
    kind = "catalog"
    # After cdli-catalog so CDLI rows already exist (we only fill ORACC-only
    # gaps); before oracc-atf (expressed via oracc-atf's runs_after).
    runs_after = ["annotation-runs", "cdli-catalog"]
    license = "CC-BY-SA-3.0"
    license_url = "https://creativecommons.org/licenses/by-sa/3.0/"
    upstream_url = "https://oracc.museum.upenn.edu/"
    citation = (
        "Open Richly Annotated Cuneiform Corpus (ORACC), "
        "https://oracc.museum.upenn.edu/ — project catalogue.json files."
    )

    def __init__(self, base: Path | None = None) -> None:
        self.base = Path(base) if base else ORACC_BASE

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Merge every ORACC catalogue.json into one record per P-number.

        First non-null value per field wins across projects (sparse first
        entries can be filled by a later project). `projects` accumulates every
        project a P-number appears in, for the oracc_projects array.
        """
        catalogues = list(_iter_catalogues(self.base))
        ctx.info("oracc_catalog.scan_start", catalogue_count=len(catalogues))

        seen: dict[str, dict] = {}
        for cat_path in catalogues:
            try:
                with open(cat_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, ValueError, OSError):
                ctx.warn("oracc_catalog.bad_json", path=str(cat_path))
                continue

            project = _clean(data.get("project")) or ""
            members = data.get("members", {})
            for key, entry in members.items():
                if not key.startswith("P") or not isinstance(entry, dict):
                    continue
                rec = seen.get(key)
                if rec is None:
                    rec = {col: None for col in FIELD_ALIASES}
                    rec["p_number"] = key
                    rec["projects"] = set()
                    seen[key] = rec
                # member-level project (falls back to file-level project)
                proj = _clean(entry.get("project")) or project
                if proj:
                    rec["projects"].add(proj)
                # first non-null per field wins
                for col, aliases in FIELD_ALIASES.items():
                    if rec[col] is None:
                        rec[col] = _pick(
                            entry,
                            aliases,
                            drop_placeholder_museum=(col == "museum_no"),
                        )

        ctx.info("oracc_catalog.merged", unique_p_numbers=len(seen))
        yield from seen.values()

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        # Tablets already cataloged (CDLI or otherwise) — never touched.
        known_p: set[str] = {
            (r["p_number"] if isinstance(r, dict) else r[0])
            for r in ctx.db.execute("SELECT p_number FROM artifacts").fetchall()
        }
        ctx.info("oracc_catalog.known_artifacts", count=len(known_p))

        # Only catalog tablets that oracc-atf can actually parse (corpusjson on
        # disk). A catalogue member without corpusjson would create an artifact
        # row that never gets text_lines — pointless and misleading.
        on_disk = _corpusjson_p_numbers(self.base)
        ctx.info("oracc_catalog.corpusjson_on_disk", count=len(on_disk))

        stats = LoadStats()
        batch: list[tuple] = []

        def _flush(cur) -> None:
            if not batch:
                return
            placeholders = ", ".join(["%s"] * len(ARTIFACT_COLUMNS))
            cur.executemany(
                f"INSERT INTO artifacts ({', '.join(ARTIFACT_COLUMNS)}) "
                f"VALUES ({placeholders}) "
                f"ON CONFLICT (p_number) DO NOTHING",
                batch,
            )
            batch.clear()

        considered = 0
        skipped_existing = 0
        skipped_no_corpusjson = 0

        with ctx.db.cursor() as cur:
            for rec in rows:
                considered += 1
                p = rec["p_number"]
                if p in known_p:
                    skipped_existing += 1
                    continue
                if p not in on_disk:
                    skipped_no_corpusjson += 1
                    continue
                projects = sorted(rec.get("projects") or [])
                values = (
                    p,
                    rec.get("designation"),
                    rec.get("period"),
                    rec.get("provenience"),
                    rec.get("genre"),
                    rec.get("subgenre"),
                    rec.get("supergenre"),
                    rec.get("language"),
                    rec.get("museum_no"),
                    rec.get("excavation_no"),
                    rec.get("primary_publication"),
                    rec.get("collection"),
                    rec.get("object_type"),
                    rec.get("material"),
                    json.dumps(projects) if projects else None,
                    "oracc",
                )
                batch.append(values)
                if len(batch) >= BATCH_SIZE:
                    _flush(cur)
                    ctx.db.commit()

            _flush(cur)
            ctx.db.commit()

        # inserted = rows that did not already exist (we filtered known_p, but
        # ON CONFLICT also guards against a concurrent insert); count via a
        # fresh query for an honest number.
        after = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM artifacts WHERE db_source = 'oracc'"
        ).fetchone()
        oracc_rows = after["n"] if isinstance(after, dict) else after[0]

        ctx.info(
            "oracc_catalog.done",
            considered=considered,
            skipped_existing=skipped_existing,
            skipped_no_corpusjson=skipped_no_corpusjson,
            artifacts_with_oracc_source=oracc_rows,
        )
        stats.inserted = oracc_rows
        stats.skipped = skipped_existing + skipped_no_corpusjson
        return stats

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n, COUNT(designation) AS d "
            "FROM artifacts WHERE db_source = 'oracc'"
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        d = row["d"] if isinstance(row, dict) else row[1]
        ctx.info("oracc_catalog.verify", oracc_artifacts=n, with_designation=d)
