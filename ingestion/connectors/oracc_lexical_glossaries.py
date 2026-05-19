"""ORACC lexical glossaries importer (lexical_lemmas + lexical_senses).

Reads gloss-*.json from ORACC projects into the unified lexical schema.
Handles multi-language support, dialect tracking, and deduplication.

Projects: dcclt, blms, etcsri, dccmt, hbtin, ribo, rinap, saao
(epsd2 handled separately by the epsd2 connector)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

ORACC_BASE = Path("source-data/sources/ORACC")

ORACC_PROJECTS = [
    # --- previously integrated ---
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

# Human-readable citation strings for source attribution; unlisted projects use "ORACC {project}".
PROJECT_CITATIONS = {
    "dcclt": "Digital Corpus of Cuneiform Lexical Texts (ORACC)",
    "blms": "Bilinguals in Late Mesopotamian Scholarship (ORACC)",
    "etcsri": "Electronic Text Corpus of Sumerian Royal Inscriptions (ORACC)",
    "dccmt": "Digital Corpus of Cuneiform Mathematical Texts (ORACC)",
    "hbtin": "Hellenistic Babylonia: Texts, Iconography, Names (ORACC)",
    "ribo": "Royal Inscriptions of Babylonia online (ORACC)",
    "rinap": "Royal Inscriptions of the Neo-Assyrian Period (ORACC)",
    "saao": "State Archives of Assyria Online (ORACC)",
    "adsd": "Astronomical Diaries Digital (ORACC)",
    "akklove": "Akkadian Love Literature (ORACC)",
    "ario": "Achaemenid Royal Inscriptions online (ORACC)",
    "armep": "Ancient Records of Middle Eastern Polities (ORACC)",
    "asbp": "Ashurbanipal Library Project (ORACC)",
    "atae": "Archival Texts of the Assyrian Empire (ORACC)",
    "babcity": "Babylonian Texts Concerning the Urban Landscape (ORACC)",
    "balt": "Babylonian Administrative and Legal Texts (ORACC)",
    "borsippa": "Archival Texts of the Priests of Borsippa (ORACC)",
    "btmao": "Babylonian Temples and Monumental Architecture online (ORACC)",
    "btto": "Babylonian Topographical Texts Online (ORACC)",
    "ckst": "Corpus of Kassite Sumerian Texts (ORACC)",
    "cmawro": "Corpus of Mesopotamian Anti-witchcraft Rituals (ORACC)",
    "ctij": "Cuneiform Texts Mentioning Israelites, Judeans, and Others (ORACC)",
    "dsst": "Datenbank sumerischer Streitliteratur (ORACC)",
    "ecut": "Electronic Corpus of Urartian Texts (ORACC)",
    "edlex": "Early Dynastic Lexical Texts (ORACC)",
    "eisl": "Electronic ISL: First Millennium Emesal Liturgies (ORACC)",
    "glass": "Corpus of Glass Technological Texts (ORACC)",
    "lacost": "Law and Order: Cuneiform Online Sustainable Tool (ORACC)",
    "nere": "Near Eastern Royal Epics (ORACC)",
    "nimrud": "Nimrud: Materialities of Assyrian Knowledge Production (ORACC)",
    "obel": "Old Babylonian Emesal Liturgies (ORACC)",
    "obmc": "Old Babylonian Model Contracts (ORACC)",
    "obta": "Old Babylonian Tabular Accounts (ORACC)",
    "oimea": "Official Inscriptions of the Middle East in Antiquity (ORACC)",
    "pnao": "Prosopography of the Neo-Assyrian Empire online (ORACC)",
    "suhu": "Inscriptions of Suhu online (ORACC)",
    "tcma": "Archival Texts of the Middle Assyrian Period (ORACC)",
    "tsae": "Textual Sources of the Assyrian Empire (ORACC)",
    "urap": "Ur Regional Archaeology Project (ORACC)",
    "cams/gkab": "CAMS Geography of Knowledge across the Babylonian World (ORACC)",
    "cams/anzu": "CAMS/Anzu Epic (ORACC)",
    "cams/barutu": "CAMS/Barutu Divination Series (ORACC)",
    "cams/etana": "CAMS/Etana Epic (ORACC)",
    "cams/ludlul": "CAMS/Ludlul bel nemeqi (ORACC)",
    "cmawro/maqlu": "Maqlû Anti-witchcraft Series (ORACC)",
    "asbp/ninmed": "Nineveh Medical Encyclopaedia (ORACC)",
}


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


def _dialect(filename: str) -> str | None:
    if "-x-" not in filename:
        return None
    base = filename.replace("gloss-", "").replace(".json", "")
    return base.split("-x-", 1)[1]


class OraccLexicalGlossariesConnector(SourceConnector):
    id = "oracc-lexical-glossaries"
    display_name = "ORACC Lexical Glossaries (lexical_lemmas)"
    description = "Imports ORACC gloss-*.json into lexical_lemmas and lexical_senses (unified schema)."
    kind = "lexicon"
    runs_after = ["epsd2"]
    license = "CC-BY-SA-3.0"
    upstream_url = "https://oracc.museum.upenn.edu/"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        for project in ORACC_PROJECTS:
            for gfile in _find_glossary_files(project):
                try:
                    with open(gfile, encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    continue
                entries = data.get("entries", [])
                if not entries:
                    continue
                language_code = _lang_code(gfile.name)
                dialect = _dialect(gfile.name)
                source = f"oracc/{project}"
                source_citation = PROJECT_CITATIONS.get(project, f"ORACC {project}")
                source_url = f"http://oracc.org/{project}"

                for entry in entries:
                    cf = entry.get("cf")
                    if not cf:
                        continue
                    yield {
                        "_target": "lexical_lemmas",
                        "citation_form": cf,
                        "guide_word": entry.get("gw"),
                        "pos": entry.get("pos"),
                        "language_code": language_code,
                        "base_form": entry.get("base"),
                        "dialect": dialect,
                        "period": None,
                        "region": None,
                        "cognates": None,
                        "derived_from": None,
                        "attestation_count": entry.get("icount", 0),
                        "tablet_count": 0,
                        "source": source,
                        "source_citation": source_citation,
                        "source_url": source_url,
                    }
                    for i, sense_data in enumerate(entry.get("senses", []), 1):
                        mng = sense_data.get("mng") or sense_data.get("sense") or ""
                        yield {
                            "_target": "lexical_senses",
                            "_lemma_cf": cf,
                            "_language_code": language_code,
                            "_source": source,
                            "sense_number": i,
                            "definition_parts": [mng] if mng else [],
                            "usage_notes": sense_data.get("note"),
                            "semantic_domain": None,
                            "typical_context": None,
                            "example_passages": [],
                            "translations": json.dumps({"en": [mng]})
                            if mng
                            else json.dumps({}),
                            "context_distribution": None,
                            "source": source,
                            "source_citation": source_citation,
                            "source_url": source_url,
                        }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        lemmas: list[dict] = []
        senses_pending: list[dict] = []

        for row in rows:
            target = row.pop("_target")
            if target == "lexical_lemmas":
                lemmas.append(row)
            else:
                senses_pending.append(row)

        stats = LoadStats()

        if lemmas:
            with ctx.db.cursor() as cur:
                cur.executemany(
                    "INSERT INTO lexical_lemmas "
                    "(citation_form, guide_word, pos, language_code, base_form, dialect, "
                    "period, region, cognates, derived_from, attestation_count, tablet_count, "
                    "source, source_citation, source_url) "
                    "VALUES (%(citation_form)s, %(guide_word)s, %(pos)s, %(language_code)s, "
                    "%(base_form)s, %(dialect)s, %(period)s, %(region)s, %(cognates)s, "
                    "%(derived_from)s, %(attestation_count)s, %(tablet_count)s, "
                    "%(source)s, %(source_citation)s, %(source_url)s) "
                    "ON CONFLICT (cf_gw_pos, source) DO NOTHING",
                    lemmas,
                )
            ctx.db.commit()
            stats.inserted += len(lemmas)

        if senses_pending:
            lemma_id_map: dict[tuple, int] = {}
            for sense in senses_pending:
                cf = sense.pop("_lemma_cf")
                language_code = sense.pop("_language_code")
                source = sense["source"]
                key = (cf, language_code, source)
                if key not in lemma_id_map:
                    row = ctx.db.execute(
                        "SELECT id FROM lexical_lemmas WHERE citation_form = %s "
                        "AND language_code = %s AND source = %s LIMIT 1",
                        (cf, language_code, source),
                    ).fetchone()
                    if row:
                        lemma_id_map[key] = (
                            row["id"] if isinstance(row, dict) else row[0]
                        )
                if key in lemma_id_map:
                    sense["lemma_id"] = lemma_id_map[key]

            senses_to_insert = [s for s in senses_pending if "lemma_id" in s]
            if senses_to_insert:
                with ctx.db.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO lexical_senses "
                        "(lemma_id, sense_number, definition_parts, usage_notes, semantic_domain, "
                        "typical_context, example_passages, translations, context_distribution, "
                        "source, source_citation, source_url) "
                        "VALUES (%(lemma_id)s, %(sense_number)s, %(definition_parts)s, "
                        "%(usage_notes)s, %(semantic_domain)s, %(typical_context)s, "
                        "%(example_passages)s, %(translations)s::jsonb, %(context_distribution)s, "
                        "%(source)s, %(source_citation)s, %(source_url)s)",
                        senses_to_insert,
                    )
                ctx.db.commit()

        return stats

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM lexical_lemmas WHERE source LIKE 'oracc/%'"
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("oracc_lexical_glossaries.verify", count=n)
