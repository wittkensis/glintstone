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

ORACC_PROJECTS = ["dcclt", "epsd2", "rinap", "saao", "blms", "cams", "etcsri", "riao"]

PROJECT_TO_RUN = {
    "dcclt": "oracc/dcclt",
    "epsd2": "oracc/epsd2",
    "rinap": "oracc/rinap",
    "saao": "oracc/saao",
    "blms": "oracc/blms",
    "cams": "oracc/cams",
    "etcsri": "oracc/etcsri",
    "riao": "oracc/riao",
}

_TABLE_KEYS = {
    "glossary_entries": ["entry_id"],
    "glossary_forms": ["entry_id", "form"],
}


def _find_glossary_files(project: str) -> list[Path]:
    base = ORACC_BASE / project / "json" / project
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
        # Load annotation_run IDs
        ann_run_ids: dict[str, int] = {}
        for proj, source_name in PROJECT_TO_RUN.items():
            row = ctx.db.execute(
                "SELECT id FROM annotation_runs WHERE source_name = %s", (source_name,)
            ).fetchone()
            if row:
                ann_run_ids[proj] = row["id"] if isinstance(row, dict) else row[0]

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
