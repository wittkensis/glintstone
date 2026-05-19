"""ORACC glossary importer (glossary_entries + glossary_forms).

Reads gloss-*.json files from ORACC projects and inserts into
glossary_entries (one row per entry) and glossary_forms (one row per form).

Depends on: annotation-runs
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector

ORACC_BASE = Path("source-data/sources/ORACC")

ORACC_PROJECTS = [
    # --- previously integrated ---
    "dcclt",
    "epsd2",
    "rinap",
    "saao",
    "blms",
    "cams",
    "etcsri",
    "riao",
    "ribo",
    "hbtin",
    "dccmt",
    "amgg",
    # --- newly added top-level ---
    "adsd",
    "akklove",
    "ario",
    "armep",
    "asbp",
    "atae",
    "babcity",
    "balt",
    "borsippa",
    "btmao",
    "btto",
    "ckst",
    "cmawro",
    "ctij",
    "dsst",
    "ecut",
    "edlex",
    "eisl",
    "glass",
    "lacost",
    "nere",
    "nimrud",
    "obel",
    "obmc",
    "obta",
    "oimea",
    "pnao",
    "suhu",
    "tcma",
    "tsae",
    "urap",
    # --- ADSD subprojects ---
    "adsd/adart1",
    "adsd/adart2",
    "adsd/adart3",
    "adsd/adart5",
    "adsd/adart6",
    # --- ASBP subprojects ---
    "asbp/ninmed",
    "asbp/rlasb",
    # --- ATAE subprojects ---
    "atae/assur",
    "atae/burmarina",
    "atae/durkatlimmu",
    "atae/durszarrukin",
    "atae/guzana",
    "atae/huzirina",
    "atae/imgurenlil",
    "atae/kalhu",
    "atae/kunalia",
    "atae/mallanate",
    "atae/marqasu",
    "atae/nineveh",
    "atae/samal",
    "atae/szibaniba",
    "atae/tilbarsip",
    "atae/tuszhan",
    # --- CAMS subprojects ---
    "cams/akno",
    "cams/anzu",
    "cams/barutu",
    "cams/etana",
    "cams/gkab",
    "cams/ludlul",
    "cams/selbi",
    # --- CMAWRO subprojects ---
    "cmawro/cmawr1",
    "cmawro/cmawr2",
    "cmawro/cmawr3",
    "cmawro/maqlu",
    # --- DCCLT subprojects ---
    "dcclt/ebla",
    "dcclt/jena",
    "dcclt/nineveh",
    "dcclt/signlists",
    # --- RIBO subprojects ---
    "ribo/babylon2",
    "ribo/babylon3",
    "ribo/babylon4",
    "ribo/babylon5",
    "ribo/babylon6",
    "ribo/babylon7",
    "ribo/babylon8",
    "ribo/babylon10",
    # --- RINAP subprojects ---
    "rinap/rinap1",
    "rinap/rinap2",
    "rinap/rinap3",
    "rinap/rinap4",
    "rinap/rinap5",
    # --- SAAO subprojects ---
    "saao/aebp",
    "saao/knpp",
    "saao/saa01",
    "saao/saa02",
    "saao/saa03",
    "saao/saa04",
    "saao/saa05",
    "saao/saa06",
    "saao/saa07",
    "saao/saa08",
    "saao/saa09",
    "saao/saa10",
    "saao/saa11",
    "saao/saa12",
    "saao/saa13",
    "saao/saa14",
    "saao/saa15",
    "saao/saa16",
    "saao/saa17",
    "saao/saa18",
    "saao/saa19",
    "saao/saa20",
    "saao/saa21",
    "saao/saas2",
    # --- other subprojects ---
    "aemw/amarna",
]

_TABLE_KEYS = {
    "glossary_entries": ["entry_id"],
    "glossary_forms": ["entry_id", "form"],
}


def _project_base(project: str) -> Path:
    parts = project.split("/")
    return ORACC_BASE.joinpath(*parts)


def _find_glossary_files(project: str) -> list[Path]:
    base = _project_base(project)
    if not base.exists():
        return []
    return sorted(base.glob("gloss-*.json"))


class OraccGlossariesConnector(SourceConnector):
    id = "oracc-glossaries"
    display_name = "ORACC Glossaries (glossary_entries)"
    description = "Imports ORACC gloss-*.json into glossary_entries and glossary_forms."
    kind = "lexicon"
    runs_after = ["annotation-runs"]
    license = "CC-BY-SA-3.0"
    upstream_url = "https://oracc.museum.upenn.edu/"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        # Load annotation_run IDs — source_name is always "oracc/{project}"
        ann_run_ids: dict[str, int] = {}
        for project in ORACC_PROJECTS:
            row = ctx.db.execute(
                "SELECT id FROM annotation_runs WHERE source_name = %s",
                (f"oracc/{project}",),
            ).fetchone()
            if row:
                ann_run_ids[project] = row["id"] if isinstance(row, dict) else row[0]

        for project in ORACC_PROJECTS:
            ann_run_id = ann_run_ids.get(project, 1)
            for gfile in _find_glossary_files(project):
                try:
                    with open(gfile, encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    continue
                lang = data.get("lang", "und")
                for entry in data.get("entries", []):
                    entry_id = entry.get("id") or entry.get("oid")
                    if not entry_id:
                        continue
                    global_id = f"{project}/{entry_id}"
                    cf = entry.get("cf", "")
                    headword = entry.get("headword", "")
                    normalized = cf.lower().strip() if cf else headword.lower().strip()
                    norms = entry.get("norms")
                    periods = entry.get("periods")
                    yield {
                        "_target": "glossary_entries",
                        "entry_id": global_id,
                        "headword": headword,
                        "citation_form": cf,
                        "guide_word": entry.get("gw", ""),
                        "language": lang,
                        "pos": entry.get("pos", ""),
                        "icount": int(entry.get("icount", 0) or 0),
                        "project": project,
                        "normalized_headword": normalized,
                        "norms": json.dumps(
                            [
                                n.get("n", "") if isinstance(n, dict) else str(n)
                                for n in norms
                            ]
                        )
                        if isinstance(norms, list)
                        else None,
                        "periods": json.dumps(periods)
                        if isinstance(periods, list)
                        else None,
                        "annotation_run_id": ann_run_id,
                    }
                    for form in entry.get("forms", []):
                        form_n = form.get("n", "")
                        if not form_n:
                            continue
                        yield {
                            "_target": "glossary_forms",
                            "entry_id": global_id,
                            "form": form_n,
                            "count": int(form.get("c", 0) or 0),
                        }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        entries: list[dict] = []
        forms: list[dict] = []
        for row in rows:
            target = row.pop("_target")
            if target == "glossary_entries":
                entries.append(row)
            else:
                forms.append(row)

        total = LoadStats()
        if entries:
            from ingestion.loader import upsert_batch

            stats = upsert_batch(
                ctx.db,
                table="glossary_entries",
                rows=entries,
                unique_key=["entry_id"],
                policy=ConflictPolicy.SKIP,
            )
            total = total.merge(stats)
        if forms:
            from ingestion.loader import upsert_batch

            stats = upsert_batch(
                ctx.db,
                table="glossary_forms",
                rows=forms,
                unique_key=["entry_id", "form"],
                policy=ConflictPolicy.SKIP,
            )
            total = total.merge(stats)
        return total

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM glossary_entries").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("oracc_glossaries.verify", count=n)
