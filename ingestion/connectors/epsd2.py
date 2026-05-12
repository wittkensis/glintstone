"""ePSD2 unified lexical importer.

Imports from ORACC ePSD2 project:
  - lexical_signs     (from epsd2-sl.json)
  - lexical_lemmas    (from gloss-sux.json)
  - lexical_senses    (from gloss-sux.json)
  - lexical_sign_lemma_associations (sign values matched to lemma citation forms)
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

EPSD2_BASE = Path("source-data/sources/ORACC/epsd2/json/epsd2")
SIGN_LIST_FILE = EPSD2_BASE / "epsd2-sl.json"
GLOSSARY_FILE = EPSD2_BASE / "gloss-sux.json"

SOURCE_CITATION = (
    "ePSD2 (Electronic Pennsylvania Sumerian Dictionary), University of Pennsylvania"
)
SOURCE_URL = "http://psd.museum.upenn.edu/epsd2/"


def _normalize_for_matching(value: str) -> str:
    no_subscripts = re.sub(r"[₀-₉]+", "", value)
    return no_subscripts.lower()


class Epsd2Connector(SourceConnector):
    id = "epsd2"
    display_name = "ePSD2 Unified Lexical Import"
    description = "Imports ePSD2 signs, lemmas, senses, and sign-lemma associations into the unified lexical schema."
    kind = "lexicon"
    runs_after = ["annotation-runs"]
    upstream_url = "http://psd.museum.upenn.edu/epsd2/"
    license = "CC-BY-SA-3.0"
    citation = SOURCE_CITATION

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        # Phase 1: signs from epsd2-sl.json
        if SIGN_LIST_FILE.exists():
            with open(SIGN_LIST_FILE, encoding="utf-8") as f:
                data = json.load(f)
            for sign_name, sign_data in data.get("signs", {}).items():
                values = [
                    unicodedata.normalize("NFC", v) for v in sign_data.get("values", [])
                ]
                yield {
                    "_target": "lexical_signs",
                    "sign_name": unicodedata.normalize("NFC", sign_name),
                    "unicode_char": None,
                    "sign_number": None,
                    "shape_category": None,
                    "component_signs": None,
                    "values": values,
                    "determinative_function": None,
                    "language_codes": ["sux"],
                    "dialects": None,
                    "periods": None,
                    "regions": None,
                    "source": "epsd2-sl",
                    "source_citation": SOURCE_CITATION,
                    "source_url": SOURCE_URL,
                }
        else:
            ctx.warn("epsd2.sign_list_missing", path=str(SIGN_LIST_FILE))

        # Phase 2: lemmas + senses from gloss-sux.json
        if GLOSSARY_FILE.exists():
            with open(GLOSSARY_FILE, encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("entries", []):
                cf = entry.get("cf")
                if not cf:
                    continue
                yield {
                    "_target": "lexical_lemmas",
                    "citation_form": cf,
                    "guide_word": entry.get("gw"),
                    "pos": entry.get("pos"),
                    "language_code": "sux",
                    "base_form": None,
                    "verbal_class": None,
                    "nominal_pattern": None,
                    "dialect": None,
                    "period": None,
                    "region": None,
                    "cognates": None,
                    "derived_from": None,
                    "attestation_count": 0,
                    "tablet_count": 0,
                    "lemma_type": "native",
                    "source": "epsd2",
                    "source_citation": SOURCE_CITATION,
                    "source_url": SOURCE_URL,
                }
                for i, sense_data in enumerate(entry.get("senses", []), 1):
                    definition = sense_data.get("mng") or sense_data.get("sense")
                    if not definition:
                        continue
                    def_parts = re.split(r"[,;]\s*", definition)
                    yield {
                        "_target": "lexical_senses",
                        "_lemma_cf": cf,
                        "sense_number": i,
                        "definition_parts": def_parts,
                        "usage_notes": None,
                        "semantic_domain": None,
                        "typical_context": None,
                        "example_passages": None,
                        "translations": json.dumps({"en": def_parts}),
                        "context_distribution": None,
                        "source": "epsd2",
                        "source_citation": SOURCE_CITATION,
                        "source_url": SOURCE_URL,
                    }
        else:
            ctx.warn("epsd2.glossary_missing", path=str(GLOSSARY_FILE))

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        signs: list[dict] = []
        lemmas: list[dict] = []
        senses_pending: list[dict] = []

        for row in rows:
            target = row.pop("_target")
            if target == "lexical_signs":
                signs.append(row)
            elif target == "lexical_lemmas":
                lemmas.append(row)
            elif target == "lexical_senses":
                senses_pending.append(row)

        stats = LoadStats()

        # Insert signs
        if signs:
            with ctx.db.cursor() as cur:
                cur.executemany(
                    "INSERT INTO lexical_signs "
                    "(sign_name, unicode_char, sign_number, shape_category, component_signs, "
                    "values, determinative_function, language_codes, dialects, periods, regions, "
                    "source, source_citation, source_url) "
                    "VALUES (%(sign_name)s, %(unicode_char)s, %(sign_number)s, %(shape_category)s, "
                    "%(component_signs)s, %(values)s, %(determinative_function)s, %(language_codes)s, "
                    "%(dialects)s, %(periods)s, %(regions)s, %(source)s, %(source_citation)s, %(source_url)s) "
                    "ON CONFLICT (sign_name, source) DO NOTHING",
                    signs,
                )
            ctx.db.commit()
            stats.inserted += len(signs)

        # Insert lemmas
        if lemmas:
            with ctx.db.cursor() as cur:
                cur.executemany(
                    "INSERT INTO lexical_lemmas "
                    "(citation_form, guide_word, pos, language_code, base_form, verbal_class, "
                    "nominal_pattern, dialect, period, region, cognates, derived_from, "
                    "attestation_count, tablet_count, lemma_type, source, source_citation, source_url) "
                    "VALUES (%(citation_form)s, %(guide_word)s, %(pos)s, %(language_code)s, %(base_form)s, "
                    "%(verbal_class)s, %(nominal_pattern)s, %(dialect)s, %(period)s, %(region)s, "
                    "%(cognates)s, %(derived_from)s, %(attestation_count)s, %(tablet_count)s, "
                    "%(lemma_type)s, %(source)s, %(source_citation)s, %(source_url)s) "
                    "ON CONFLICT (cf_gw_pos, source) DO NOTHING",
                    lemmas,
                )
            ctx.db.commit()

        # Resolve lemma IDs and insert senses
        if senses_pending:
            lemma_id_map: dict[str, int] = {}
            for sense in senses_pending:
                cf = sense.pop("_lemma_cf")
                if cf not in lemma_id_map:
                    row = ctx.db.execute(
                        "SELECT id FROM lexical_lemmas WHERE citation_form = %s AND source = 'epsd2' LIMIT 1",
                        (cf,),
                    ).fetchone()
                    if row:
                        lemma_id_map[cf] = (
                            row["id"] if isinstance(row, dict) else row[0]
                        )
                if cf in lemma_id_map:
                    sense["lemma_id"] = lemma_id_map[cf]

            senses_to_insert = [s for s in senses_pending if "lemma_id" in s]
            if senses_to_insert:
                with ctx.db.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO lexical_senses "
                        "(lemma_id, sense_number, definition_parts, usage_notes, semantic_domain, "
                        "typical_context, example_passages, translations, context_distribution, "
                        "source, source_citation, source_url) "
                        "VALUES (%(lemma_id)s, %(sense_number)s, %(definition_parts)s, %(usage_notes)s, "
                        "%(semantic_domain)s, %(typical_context)s, %(example_passages)s, "
                        "%(translations)s::jsonb, %(context_distribution)s, %(source)s, "
                        "%(source_citation)s, %(source_url)s)",
                        senses_to_insert,
                    )
                ctx.db.commit()

        # Phase 3: sign-lemma associations
        if signs:
            self._create_associations(ctx, signs)

        return stats

    def _create_associations(self, ctx: RunContext, signs: list[dict]) -> None:
        associations = []
        for sign in signs:
            sign_row = ctx.db.execute(
                "SELECT id FROM lexical_signs WHERE sign_name = %s AND source = 'epsd2-sl' LIMIT 1",
                (sign["sign_name"],),
            ).fetchone()
            if not sign_row:
                continue
            sign_id = sign_row["id"] if isinstance(sign_row, dict) else sign_row[0]
            for value in sign.get("values", []):
                normalized = _normalize_for_matching(value)
                lemma_row = ctx.db.execute(
                    "SELECT id FROM lexical_lemmas WHERE LOWER(citation_form) = %s "
                    "AND language_code = 'sux' AND source = 'epsd2' LIMIT 1",
                    (normalized,),
                ).fetchone()
                if lemma_row:
                    associations.append(
                        {
                            "sign_id": sign_id,
                            "lemma_id": lemma_row["id"]
                            if isinstance(lemma_row, dict)
                            else lemma_row[0],
                            "value": value,
                            "reading_type": "logographic",
                            "frequency": 0,
                            "context_distribution": None,
                            "source": "epsd2-sl",
                            "source_citation": SOURCE_CITATION,
                            "source_url": SOURCE_URL,
                        }
                    )
        if associations:
            with ctx.db.cursor() as cur:
                cur.executemany(
                    "INSERT INTO lexical_sign_lemma_associations "
                    "(sign_id, lemma_id, value, reading_type, frequency, context_distribution, "
                    "source, source_citation, source_url) "
                    "VALUES (%(sign_id)s, %(lemma_id)s, %(value)s, %(reading_type)s, %(frequency)s, "
                    "%(context_distribution)s, %(source)s, %(source_citation)s, %(source_url)s) "
                    "ON CONFLICT DO NOTHING",
                    associations,
                )
            ctx.db.commit()
            ctx.info("epsd2.associations_created", count=len(associations))

    def verify(self, ctx: RunContext) -> None:
        for table, minimum in (("lexical_signs", 100), ("lexical_lemmas", 1000)):
            row = ctx.db.execute(
                f"SELECT COUNT(*) AS n FROM {table} WHERE source LIKE 'epsd2%'"
            ).fetchone()
            n = row["n"] if isinstance(row, dict) else row[0]
            ctx.info(f"epsd2.verify.{table}", count=n)
            if n < minimum:
                raise AssertionError(
                    f"{table} (epsd2) has {n} rows; expected ≥ {minimum}"
                )
