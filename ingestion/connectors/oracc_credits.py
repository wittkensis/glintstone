"""ORACC per-text credits importer.

Reads credits field from each ORACC catalogue.json and stores one row per
(p_number, oracc_project) in artifact_credits. Q-numbers are resolved to
P-numbers via the artifact_composites table.

Depends on: cdli-catalog (artifacts must be loaded)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector
from ingestion.loader import upsert_batch

ORACC_BASE = Path("source-data/sources/ORACC")

# Top-level and subproject slugs — subprojects use "parent/child" form.
# All produce catalogue.json; connectors skip gracefully if the file is absent.
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
    "rimanum",
    "etcsl",
    "ribo",
    "rime",
    "amgg",
    "hbtin",
    "dccmt",
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
    "iraq",
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
    # --- ADSD subprojects (Astronomical Diaries) ---
    "adsd/adart1",
    "adsd/adart2",
    "adsd/adart3",
    "adsd/adart5",
    "adsd/adart6",
    # --- ASBP subprojects (Ashurbanipal Library) ---
    "asbp/ninmed",
    "asbp/rlasb",
    # --- ATAE subprojects (Neo-Assyrian Archival Texts by site) ---
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
    # --- CAMS subprojects (Corpus of Ancient Mesopotamian Scholarship) ---
    "cams/akno",
    "cams/anzu",
    "cams/barutu",
    "cams/etana",
    "cams/gkab",
    "cams/ludlul",
    "cams/ntlab",
    "cams/selbi",
    # --- CMAWRO subprojects (Anti-witchcraft Rituals) ---
    "cmawro/cmawr1",
    "cmawro/cmawr2",
    "cmawro/cmawr3",
    "cmawro/maqlu",
    # --- DCCLT subprojects ---
    "dcclt/ebla",
    "dcclt/jena",
    "dcclt/nineveh",
    "dcclt/signlists",
    # --- RIBO subprojects (Royal Inscriptions of Babylonia by dynasty) ---
    "ribo/babylon2",
    "ribo/babylon3",
    "ribo/babylon4",
    "ribo/babylon5",
    "ribo/babylon6",
    "ribo/babylon7",
    "ribo/babylon8",
    "ribo/babylon10",
    # --- RINAP subprojects (Royal Inscriptions of Neo-Assyrian Period by king) ---
    "rinap/rinap1",
    "rinap/rinap2",
    "rinap/rinap3",
    "rinap/rinap4",
    "rinap/rinap5",
    # --- SAAO subprojects (State Archives of Assyria volumes) ---
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


def _project_base(project: str) -> Path:
    parts = project.split("/")
    return ORACC_BASE.joinpath(*parts)


def _find_catalogue(project: str) -> Path | None:
    base = _project_base(project)
    for candidate in [base / "catalogue.json", base.parent / "catalogue.json"]:
        if candidate.exists():
            return candidate
    return None


class OraccCreditsConnector(SourceConnector):
    id = "oracc-credits"
    display_name = "ORACC Per-Text Credits"
    description = (
        "Imports artifact_credits rows from ORACC catalogue.json credit fields."
    )
    kind = "catalog"
    runs_after = ["cdli-catalog"]
    license = "CC-BY-SA-3.0"
    upstream_url = "https://oracc.museum.upenn.edu/"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        # Load Q→P and valid-P maps once
        q_to_p: dict[str, list[str]] = {}
        for row in ctx.db.execute(
            "SELECT q_number, p_number FROM artifact_composites"
        ).fetchall():
            q, p = (
                (row["q_number"], row["p_number"])
                if isinstance(row, dict)
                else (row[0], row[1])
            )
            q_to_p.setdefault(q, []).append(p)

        valid_p = {
            (row["p_number"] if isinstance(row, dict) else row[0])
            for row in ctx.db.execute("SELECT p_number FROM artifacts").fetchall()
        }
        ctx.info(
            "oracc_credits.loaded_maps", q_numbers=len(q_to_p), p_numbers=len(valid_p)
        )

        for project in ORACC_PROJECTS:
            cat_path = _find_catalogue(project)
            if not cat_path:
                continue
            try:
                with open(cat_path, encoding="utf-8") as f:
                    catalogue = json.load(f)
            except (json.JSONDecodeError, ValueError):
                ctx.warn("oracc_credits.bad_json", project=project)
                continue

            for text_id, entry in catalogue.get("members", {}).items():
                credits = entry.get("credits", "").strip()
                if not credits:
                    continue
                p_numbers: list[str] = []
                if text_id.startswith("P"):
                    p_numbers = [text_id]
                elif text_id.startswith("Q"):
                    p_numbers = q_to_p.get(text_id, [])
                for p_number in p_numbers:
                    if p_number not in valid_p:
                        continue
                    yield {
                        "p_number": p_number,
                        "oracc_project": project,
                        "credits_text": credits,
                    }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(
            ctx.db,
            table="artifact_credits",
            rows=rows,
            unique_key=["p_number", "oracc_project"],
            policy=ConflictPolicy.SKIP,
            batch_size=500,
        )

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM artifact_credits").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("oracc_credits.verify", count=n)
