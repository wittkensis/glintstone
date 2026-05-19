"""ORACC normalization bridge importer.

Reads norms and norm-forms from ORACC glossary entry.norms[] arrays into:
  - lexical_norms (normalized forms linked to lemmas)
  - lexical_norm_forms (written/orthographic spellings per norm)

Then backfills lemmatizations.norm_id FK from existing TEXT norm values.

Depends on: oracc-lexical-glossaries, epsd2 (lexical_lemmas must be populated)
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

ORACC_BASE = Path("source-data/sources/ORACC")

ALL_PROJECTS = [
    # --- previously integrated ---
    "epsd2",
    "dcclt",
    "blms",
    "etcsri",
    "dccmt",
    "hbtin",
    "ribo",
    "rinap",
    "saao",
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


def _project_base(project: str) -> Path:
    parts = project.split("/")
    return ORACC_BASE.joinpath(*parts)


def _find_glossary_files(project: str) -> list[Path]:
    base = _project_base(project)
    if not base.exists():
        return []
    return sorted(base.glob("gloss-*.json"))


def _lang_code(filename: str) -> str:
    base = filename.replace("gloss-", "").replace(".json", "")
    return base.split("-x-")[0] if "-x-" in base else base


def _build_lemma_cache(db) -> dict:
    cache: dict[tuple, int] = {}
    for row in db.execute(
        "SELECT id, citation_form, guide_word, pos, language_code, source FROM lexical_lemmas"
    ).fetchall():
        if isinstance(row, dict):
            key = (
                row["citation_form"],
                row["guide_word"],
                row["pos"],
                row["language_code"],
                row["source"],
            )
            cache[key] = row["id"]
        else:
            key = (row[1], row[2], row[3], row[4], row[5])
            cache[key] = row[0]
    return cache


class OraccNormsConnector(SourceConnector):
    id = "oracc-norms"
    display_name = "ORACC Normalization Bridge"
    description = "Imports lexical_norms and lexical_norm_forms from ORACC glossary norms arrays, then backfills lemmatizations.norm_id."
    kind = "lexicon"
    runs_after = ["oracc-lexical-glossaries", "epsd2", "oracc-lemmatizations"]
    license = "CC-BY-SA-3.0"
    upstream_url = "https://oracc.museum.upenn.edu/"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        lemma_cache = _build_lemma_cache(ctx.db)
        ctx.info("oracc_norms.lemma_cache", count=len(lemma_cache))

        for project in ALL_PROJECTS:
            for gfile in _find_glossary_files(project):
                try:
                    with open(gfile, encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    continue

                language_code = _lang_code(gfile.name)
                source = "epsd2" if project == "epsd2" else f"oracc/{project}"

                for entry in data.get("entries", []):
                    cf = entry.get("cf")
                    gw = entry.get("gw")
                    pos = entry.get("pos")
                    norms_data = entry.get("norms", [])
                    if not norms_data or not cf:
                        continue
                    lemma_id = lemma_cache.get((cf, gw, pos, language_code, source))
                    if not lemma_id:
                        continue
                    for norm_entry in norms_data:
                        norm_text = norm_entry.get("n")
                        if not norm_text:
                            continue
                        forms = [
                            {
                                "form": unicodedata.normalize("NFC", fe["n"]),
                                "icount": int(fe.get("icount", 0)),
                            }
                            for fe in norm_entry.get("forms", [])
                            if fe.get("n")
                        ]
                        yield {
                            "norm": norm_text,
                            "lemma_id": lemma_id,
                            "attestation_count": int(norm_entry.get("icount", 0)),
                            "attestation_pct": int(norm_entry.get("ipct", 0)),
                            "source": source,
                            "source_id": norm_entry.get("id"),
                            "_forms": forms,
                        }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        norms_batch: list[dict] = []
        forms_pending: list[dict] = []

        for row in rows:
            forms = row.pop("_forms")
            norms_batch.append(row)
            norm_key = (row["norm"], row["lemma_id"], row["source"])
            for form in forms:
                forms_pending.append(
                    {
                        "norm_key": norm_key,
                        "written_form": form["form"],
                        "attestation_count": form["icount"],
                        "source": row["source"],
                    }
                )

        stats = LoadStats()

        if norms_batch:
            with ctx.db.cursor() as cur:
                cur.executemany(
                    "INSERT INTO lexical_norms "
                    "(norm, lemma_id, attestation_count, attestation_pct, source, source_id) "
                    "VALUES (%(norm)s, %(lemma_id)s, %(attestation_count)s, %(attestation_pct)s, "
                    "%(source)s, %(source_id)s) "
                    "ON CONFLICT (norm, lemma_id, source) DO NOTHING",
                    norms_batch,
                )
            ctx.db.commit()
            stats.inserted += len(norms_batch)

        if forms_pending:
            # Build norm_id cache
            norm_id_cache: dict[tuple, int] = {}
            unique_keys = {nf["norm_key"] for nf in forms_pending}
            for norm_text, lemma_id, src in unique_keys:
                row = ctx.db.execute(
                    "SELECT id FROM lexical_norms WHERE norm = %s AND lemma_id = %s AND source = %s",
                    (norm_text, lemma_id, src),
                ).fetchone()
                if row:
                    norm_id_cache[(norm_text, lemma_id, src)] = (
                        row["id"] if isinstance(row, dict) else row[0]
                    )

            forms_to_insert = []
            for nf in forms_pending:
                norm_id = norm_id_cache.get(nf["norm_key"])
                if norm_id:
                    forms_to_insert.append(
                        {
                            "norm_id": norm_id,
                            "written_form": nf["written_form"],
                            "attestation_count": nf["attestation_count"],
                            "source": nf["source"],
                        }
                    )

            if forms_to_insert:
                with ctx.db.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO lexical_norm_forms "
                        "(norm_id, written_form, attestation_count, source) "
                        "VALUES (%(norm_id)s, %(written_form)s, %(attestation_count)s, %(source)s) "
                        "ON CONFLICT (norm_id, written_form) DO NOTHING",
                        forms_to_insert,
                    )
                ctx.db.commit()

        # Backfill lemmatizations.norm_id
        ctx.info("oracc_norms.backfill_start")
        ctx.db.execute("""
            UPDATE lemmatizations l
            SET norm_id = ln.id
            FROM lexical_norms ln
            JOIN lexical_lemmas ll ON ln.lemma_id = ll.id
            WHERE l.norm IS NOT NULL
              AND l.norm != ''
              AND l.norm_id IS NULL
              AND l.norm = ln.norm
              AND l.citation_form = ll.citation_form
              AND l.guide_word = ll.guide_word
              AND l.language LIKE ll.language_code || '%'
        """)
        ctx.db.commit()

        # Update pipeline_status linguistic completeness
        ctx.db.execute("""
            UPDATE pipeline_status ps
            SET linguistic_complete = 1.0
            WHERE (linguistic_complete IS NULL OR linguistic_complete = 0)
            AND EXISTS (
                SELECT 1 FROM lemmatizations l
                JOIN tokens t ON l.token_id = t.id
                JOIN text_lines tl ON t.line_id = tl.id
                WHERE tl.p_number = ps.p_number
                AND l.citation_form IS NOT NULL AND l.citation_form != ''
            )
        """)
        ctx.db.execute("""
            UPDATE pipeline_status ps
            SET linguistic_complete = 0.5
            WHERE (linguistic_complete IS NULL OR linguistic_complete = 0)
            AND EXISTS (
                SELECT 1 FROM lemmatizations l
                JOIN tokens t ON l.token_id = t.id
                JOIN text_lines tl ON t.line_id = tl.id
                WHERE tl.p_number = ps.p_number AND l.norm_id IS NOT NULL
            )
        """)
        ctx.db.commit()

        return stats

    def verify(self, ctx: RunContext) -> None:
        for table in ("lexical_norms", "lexical_norm_forms"):
            row = ctx.db.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
            n = row["n"] if isinstance(row, dict) else row[0]
            ctx.info(f"oracc_norms.verify.{table}", count=n)
