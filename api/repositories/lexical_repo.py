"""Lexical repository — browse signs, lemmas, and meanings with filters."""

import math
from collections import defaultdict

from core.repository import BaseRepository

# POS code → full label
POS_LABELS = {
    "N": "Noun",
    "V": "Verb",
    "AJ": "Adjective",
    "AV": "Adverb",
    "PN": "Personal Name",
    "DN": "Divine Name",
    "GN": "Geographical Name",
    "SN": "Settlement Name",
    "RN": "Royal Name",
    "TN": "Temple Name",
    "EN": "Ethnic Name",
    "WN": "Watercourse Name",
    "MN": "Month Name",
    "ON": "Object Name",
    "CN": "Calendar Name",
    "FN": "Field Name",
    "QN": "Quarter Name",
    "LN": "Line Name",
    "V/t": "Verb (transitive)",
    "V/i": "Verb (intransitive)",
    "DP": "Demonstrative Pronoun",
    "IP": "Indefinite Pronoun",
    "PP": "Preposition",
    "PRP": "Preposition",
    "NU": "Number",
    "CNJ": "Conjunction",
    "MOD": "Modal Particle",
    "J": "Interjection",
    "XP": "Particle",
    "DET": "Determiner",
    "SBJ": "Subjunction",
    "REL": "Relative Pronoun",
    "RP": "Reflexive Pronoun",
    "QP": "Proper Noun",
    "MA": "Measure",
    "O": "Other",
    "U": "Unknown",
    "M": "Modifier",
    "X": "Unclassified",
}

# Source code → display label
SOURCE_LABELS = {
    "epsd2": "ePSD2",
    "epsd2-sl": "ePSD2 Sign List",
    "ebl-sign-list": "eBL Sign List",
    "unicode-standard": "Unicode Standard",
    "oracc/dcclt": "ORACC/DCCLT",
    "oracc/saao": "ORACC/SAAo",
    "oracc/rinap": "ORACC/RINAP",
    "oracc/blms": "ORACC/BLMS",
    "oracc/ribo": "ORACC/RIBo",
    "oracc/etcsri": "ORACC/ETCSRI",
    "oracc/hbtin": "ORACC/HBTIN",
    "oracc/dccmt": "ORACC/DCCMT",
}


def pos_label(code: str) -> str:
    return POS_LABELS.get(code, code)


def source_label(code: str) -> str:
    return SOURCE_LABELS.get(code, code)


LANG_FALLBACK = {
    "qpn": "Proper Noun",
    "xhu": "Hurrian",
    "uga": "Ugaritic",
    "elx": "Elamite",
    "hit": "Hittite",
    "arc": "Aramaic",
    "peo": "Old Persian",
    "grc": "Greek",
}


class LexicalRepository(BaseRepository):
    # ── Language helper (cached per request) ──────────────────

    def _lang_map(self) -> dict[str, str]:
        """oracc_code → full_name from language_map table."""
        if not hasattr(self, "_lang_cache"):
            rows = self.fetch_all(
                "SELECT DISTINCT oracc_code, full_name FROM language_map"
            )
            self._lang_cache = dict(LANG_FALLBACK)
            for r in rows:
                code = r["oracc_code"]
                name = r["full_name"]
                # Skip uncertain/compound entries — keep shortest name per code
                if code not in self._lang_cache or len(name) < len(
                    self._lang_cache[code]
                ):
                    self._lang_cache[code] = name
        return self._lang_cache

    def lang_label(self, code: str) -> str:
        return self._lang_map().get(code, code)

    # ── Browse lemmas ─────────────────────────────────────────

    def browse_lemmas(
        self,
        search: str | None = None,
        language: list[str] | None = None,
        pos: list[str] | None = None,
        source: list[str] | None = None,
        frequency: str | None = None,
        sort: str = "frequency",
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        conditions: list[str] = []
        params: dict = {}

        if search:
            conditions.append(
                "(l.citation_form ILIKE %(search)s " "OR l.guide_word ILIKE %(search)s)"
            )
            params["search"] = f"%{search}%"
        if language:
            # Language family matching (akk includes akk-x-stdbab)
            lang_conds = []
            for i, lang in enumerate(language):
                k = f"lang{i}"
                lang_conds.append(
                    f"(l.language_code = %({k})s "
                    f"OR l.language_code LIKE %({k}_fam)s)"
                )
                params[k] = lang
                params[f"{k}_fam"] = f"{lang}-%"
            conditions.append(f"({' OR '.join(lang_conds)})")
        if pos:
            clause, p = self.build_in_clause(pos, prefix="pos")
            conditions.append(f"l.pos {clause}")
            params.update(p)
        if source:
            clause, p = self.build_in_clause(source, prefix="src")
            conditions.append(f"l.source {clause}")
            params.update(p)
        if frequency:
            conditions.append(self._freq_condition(frequency))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * per_page
        params["per_page"] = per_page
        params["offset"] = offset

        order = (
            "ORDER BY l.attestation_count DESC NULLS LAST, l.citation_form"
            if sort != "alpha"
            else "ORDER BY l.citation_form, l.attestation_count DESC NULLS LAST"
        )

        items = self.fetch_all(
            f"""
            SELECT l.id, l.citation_form, l.guide_word, l.pos,
                   l.language_code, l.attestation_count, l.source,
                   (SELECT array_agg(DISTINCT dp)
                    FROM lexical_senses s,
                         LATERAL unnest(s.definition_parts) dp
                    WHERE s.lemma_id = l.id
                   ) AS meanings
            FROM lexical_lemmas l
            {where}
            {order}
            LIMIT %(per_page)s OFFSET %(offset)s
        """,
            params,
        )

        count_params = {
            k: v for k, v in params.items() if k not in ("per_page", "offset")
        }
        total = (
            self.fetch_scalar(
                f"SELECT COUNT(*) FROM lexical_lemmas l {where}", count_params
            )
            or 0
        )

        # Enrich with labels
        lm = self._lang_map()
        for item in items:
            item["language_label"] = lm.get(
                item["language_code"], item["language_code"]
            )
            item["pos_label"] = pos_label(item["pos"]) if item["pos"] else ""
            item["source_label"] = source_label(item["source"])
            if not item["meanings"]:
                item["meanings"] = []

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page) if per_page else 0,
        }

    # ── Browse signs ──────────────────────────────────────────

    def browse_signs(
        self,
        search: str | None = None,
        language: list[str] | None = None,
        source: list[str] | None = None,
        sort: str = "name",
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        conditions: list[str] = []
        params: dict = {}

        if search:
            conditions.append(
                "(s.sign_name ILIKE %(search)s OR %(search_exact)s = ANY(s.values))"
            )
            params["search"] = f"%{search}%"
            params["search_exact"] = search.lower()
        if language:
            # Check if any of the selected languages overlap with sign's language_codes
            lang_conds = []
            for i, lang in enumerate(language):
                k = f"lang{i}"
                lang_conds.append(f"%({k})s = ANY(s.language_codes)")
                params[k] = lang
            conditions.append(f"({' OR '.join(lang_conds)})")
        if source:
            clause, p = self.build_in_clause(source, prefix="src")
            conditions.append(f"s.source {clause}")
            params.update(p)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * per_page
        params["per_page"] = per_page
        params["offset"] = offset

        order = (
            "ORDER BY s.sign_name"
            if sort == "name"
            else "ORDER BY lemma_count DESC NULLS LAST, s.sign_name"
        )

        items = self.fetch_all(
            f"""
            SELECT s.id, s.sign_name, s.unicode_char,
                   s.source, s.values,
                   COUNT(DISTINCT sla.lemma_id) AS lemma_count,
                   array_length(s.values, 1) AS reading_count,
                   (SELECT array_agg(DISTINCT dp)
                    FROM lexical_sign_lemma_associations sla2
                    JOIN lexical_senses sen ON sen.lemma_id = sla2.lemma_id
                    CROSS JOIN LATERAL unnest(sen.definition_parts) dp
                    WHERE sla2.sign_id = s.id
                    LIMIT 1
                   ) AS meanings
            FROM lexical_signs s
            LEFT JOIN lexical_sign_lemma_associations sla ON s.id = sla.sign_id
            {where}
            GROUP BY s.id
            {order}
            LIMIT %(per_page)s OFFSET %(offset)s
        """,
            params,
        )

        count_params = {
            k: v for k, v in params.items() if k not in ("per_page", "offset")
        }
        total = (
            self.fetch_scalar(
                f"""SELECT COUNT(DISTINCT s.id) FROM lexical_signs s
                    LEFT JOIN lexical_sign_lemma_associations sla ON s.id = sla.sign_id
                    {where}""",
                count_params,
            )
            or 0
        )

        for item in items:
            item["source_label"] = source_label(item["source"])
            if not item["meanings"]:
                item["meanings"] = []
            if not item["reading_count"]:
                item["reading_count"] = 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page) if per_page else 0,
        }

    # ── Browse meanings (grouped by guide_word) ───────────────

    def browse_meanings(
        self,
        search: str | None = None,
        language: list[str] | None = None,
        pos: list[str] | None = None,
        sort: str = "attestations",
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        conditions: list[str] = []
        params: dict = {}

        if search:
            conditions.append("l.guide_word ILIKE %(search)s")
            params["search"] = f"%{search}%"
        if language:
            lang_conds = []
            for i, lang in enumerate(language):
                k = f"lang{i}"
                lang_conds.append(
                    f"(l.language_code = %({k})s "
                    f"OR l.language_code LIKE %({k}_fam)s)"
                )
                params[k] = lang
                params[f"{k}_fam"] = f"{lang}-%"
            conditions.append(f"({' OR '.join(lang_conds)})")
        if pos:
            clause, p = self.build_in_clause(pos, prefix="pos")
            conditions.append(f"l.pos {clause}")
            params.update(p)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        # Must also filter out null/empty guide_words
        if where:
            where += " AND l.guide_word IS NOT NULL AND l.guide_word <> ''"
        else:
            where = "WHERE l.guide_word IS NOT NULL AND l.guide_word <> ''"

        offset = (page - 1) * per_page
        params["per_page"] = per_page
        params["offset"] = offset

        order = (
            "ORDER BY total_attestations DESC NULLS LAST, l.guide_word"
            if sort != "alpha"
            else "ORDER BY l.guide_word, total_attestations DESC NULLS LAST"
        )

        items = self.fetch_all(
            f"""
            SELECT l.guide_word,
                   MODE() WITHIN GROUP (ORDER BY l.pos) AS pos,
                   COUNT(DISTINCT l.id) AS lemma_count,
                   COUNT(DISTINCT l.language_code) AS language_count,
                   SUM(l.attestation_count) AS total_attestations,
                   json_agg(DISTINCT jsonb_build_object(
                       'lang', l.language_code,
                       'cf', l.citation_form
                   )) AS lemmas_by_lang
            FROM lexical_lemmas l
            {where}
            GROUP BY l.guide_word
            {order}
            LIMIT %(per_page)s OFFSET %(offset)s
        """,
            params,
        )

        count_params = {
            k: v for k, v in params.items() if k not in ("per_page", "offset")
        }
        total = (
            self.fetch_scalar(
                f"""SELECT COUNT(DISTINCT l.guide_word)
                    FROM lexical_lemmas l {where}""",
                count_params,
            )
            or 0
        )

        lm = self._lang_map()
        for item in items:
            item["pos_label"] = pos_label(item["pos"]) if item["pos"] else ""
            # Group lemma citation_forms by language
            by_lang: dict[str, list[str]] = defaultdict(list)
            if item["lemmas_by_lang"]:
                for entry in item["lemmas_by_lang"]:
                    lang = entry["lang"]
                    cf = entry["cf"]
                    if cf not in by_lang[lang]:
                        by_lang[lang].append(cf)
            item["lemmas_grouped"] = {lm.get(k, k): v for k, v in by_lang.items()}

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page) if per_page else 0,
        }

    # ── Detail endpoints (for right panel) ────────────────────

    def get_lemma_detail(self, lemma_id: int) -> dict | None:
        lemma = self.fetch_one(
            "SELECT * FROM lexical_lemmas WHERE id = %(id)s", {"id": lemma_id}
        )
        if not lemma:
            return None

        senses = self.fetch_all(
            """SELECT DISTINCT ON (sense_number, definition_parts)
                   id, sense_number, definition_parts, usage_notes,
                   semantic_domain, source
               FROM lexical_senses
               WHERE lemma_id = %(id)s
               ORDER BY sense_number, definition_parts""",
            {"id": lemma_id},
        )

        signs = self.fetch_all(
            """SELECT s.id, s.sign_name, s.unicode_char,
                      sla.reading_type, sla.value
               FROM lexical_signs s
               JOIN lexical_sign_lemma_associations sla ON s.id = sla.sign_id
               WHERE sla.lemma_id = %(id)s
               ORDER BY sla.frequency DESC NULLS LAST""",
            {"id": lemma_id},
        )

        lm = self._lang_map()
        lemma["language_label"] = lm.get(lemma["language_code"], lemma["language_code"])
        lemma["pos_label"] = pos_label(lemma["pos"]) if lemma["pos"] else ""
        lemma["source_label"] = source_label(lemma["source"])

        return {"lemma": lemma, "senses": senses, "signs": signs}

    def get_sign_detail(self, sign_id: int) -> dict | None:
        sign = self.fetch_one(
            "SELECT * FROM lexical_signs WHERE id = %(id)s", {"id": sign_id}
        )
        if not sign:
            return None

        lemmas = self.fetch_all(
            """SELECT l.id, l.citation_form, l.guide_word, l.pos,
                      l.language_code, l.attestation_count,
                      sla.reading_type, sla.value
               FROM lexical_lemmas l
               JOIN lexical_sign_lemma_associations sla ON l.id = sla.lemma_id
               WHERE sla.sign_id = %(id)s
               ORDER BY l.attestation_count DESC NULLS LAST""",
            {"id": sign_id},
        )

        lm = self._lang_map()
        sign["source_label"] = source_label(sign["source"])
        for lem in lemmas:
            lem["language_label"] = lm.get(lem["language_code"], lem["language_code"])
            lem["pos_label"] = pos_label(lem["pos"]) if lem["pos"] else ""

        return {"sign": sign, "lemmas": lemmas}

    def get_meaning_detail(
        self, guide_word: str, pos: str | None = None
    ) -> dict | None:
        conditions = ["l.guide_word = %(gw)s"]
        params: dict = {"gw": guide_word}
        if pos:
            conditions.append("l.pos = %(pos)s")
            params["pos"] = pos

        where = "WHERE " + " AND ".join(conditions)

        lemmas = self.fetch_all(
            f"""SELECT l.id, l.citation_form, l.guide_word, l.pos,
                       l.language_code, l.attestation_count, l.source,
                       (SELECT array_agg(DISTINCT dp)
                        FROM lexical_senses s,
                             LATERAL unnest(s.definition_parts) dp
                        WHERE s.lemma_id = l.id
                       ) AS meanings
                FROM lexical_lemmas l
                {where}
                ORDER BY l.attestation_count DESC NULLS LAST""",
            params,
        )

        if not lemmas:
            return None

        lm = self._lang_map()
        for lem in lemmas:
            lem["language_label"] = lm.get(lem["language_code"], lem["language_code"])
            lem["pos_label"] = pos_label(lem["pos"]) if lem["pos"] else ""
            lem["source_label"] = source_label(lem["source"])
            if not lem["meanings"]:
                lem["meanings"] = []

        return {
            "guide_word": guide_word,
            "pos": pos,
            "pos_label": pos_label(pos) if pos else "",
            "lemmas": lemmas,
            "total_attestations": sum(
                (row["attestation_count"] or 0) for row in lemmas
            ),
        }

    # ── Filter options ────────────────────────────────────────

    def get_filter_options(
        self,
        level: str,
        active_filters: dict[str, list[str]] | None = None,
    ) -> dict:
        af = active_filters or {}
        options: dict = {}

        if level == "signs":
            options["language"] = self._sign_language_counts(af)
            options["source"] = self._sign_source_counts(af)
        elif level == "lemmas":
            options["language"] = self._lemma_language_counts(af)
            options["pos"] = self._lemma_pos_counts(af)
            options["source"] = self._lemma_source_counts(af)
            options["frequency"] = self._lemma_frequency_counts(af)
        elif level == "meanings":
            options["language"] = self._meaning_language_counts(af)
            options["pos"] = self._meaning_pos_counts(af)

        return options

    # ── Filter count helpers ──────────────────────────────────

    def _lemma_where(self, af: dict, exclude: str) -> tuple[str, dict]:
        """Build WHERE for lemma-level cross-filter counts."""
        conditions: list[str] = []
        params: dict = {}
        for dim, values in af.items():
            if dim == exclude or not values:
                continue
            if dim == "language":
                lang_conds = []
                for i, lang in enumerate(values):
                    k = f"xf_lang{i}"
                    lang_conds.append(
                        f"(l.language_code = %({k})s "
                        f"OR l.language_code LIKE %({k}_fam)s)"
                    )
                    params[k] = lang
                    params[f"{k}_fam"] = f"{lang}-%"
                conditions.append(f"({' OR '.join(lang_conds)})")
            elif dim == "pos":
                clause, p = self.build_in_clause(values, prefix="xf_pos")
                conditions.append(f"l.pos {clause}")
                params.update(p)
            elif dim == "source":
                clause, p = self.build_in_clause(values, prefix="xf_src")
                conditions.append(f"l.source {clause}")
                params.update(p)
            elif dim == "frequency":
                if values:
                    conditions.append(self._freq_condition(values[0]))
        return (" AND ".join(conditions), params) if conditions else ("", {})

    def _lemma_language_counts(self, af: dict) -> list[dict]:
        xf, params = self._lemma_where(af, "language")
        where = f"WHERE {xf}" if xf else ""
        rows = self.fetch_all(
            f"""
            SELECT
                CASE
                    WHEN l.language_code LIKE 'akk%%' THEN 'akk'
                    WHEN l.language_code LIKE 'sux%%' THEN 'sux'
                    ELSE l.language_code
                END AS code,
                COUNT(*) AS count
            FROM lexical_lemmas l
            {where}
            GROUP BY code
            HAVING COUNT(*) > 0
            ORDER BY count DESC
        """,
            params,
        )
        lm = self._lang_map()
        return [
            {
                "val": r["code"],
                "label": lm.get(r["code"], r["code"]),
                "count": r["count"],
            }
            for r in rows
        ]

    def _lemma_pos_counts(self, af: dict) -> list[dict]:
        xf, params = self._lemma_where(af, "pos")
        where = (
            f"WHERE l.pos IS NOT NULL AND l.pos <> '' AND {xf}"
            if xf
            else "WHERE l.pos IS NOT NULL AND l.pos <> ''"
        )
        rows = self.fetch_all(
            f"""
            SELECT l.pos AS code, COUNT(*) AS count
            FROM lexical_lemmas l
            {where}
            GROUP BY l.pos
            ORDER BY count DESC
        """,
            params,
        )
        return [
            {"val": r["code"], "label": pos_label(r["code"]), "count": r["count"]}
            for r in rows
        ]

    def _lemma_source_counts(self, af: dict) -> list[dict]:
        xf, params = self._lemma_where(af, "source")
        where = f"WHERE {xf}" if xf else ""
        rows = self.fetch_all(
            f"""
            SELECT l.source AS code, COUNT(*) AS count
            FROM lexical_lemmas l
            {where}
            GROUP BY l.source
            ORDER BY count DESC
        """,
            params,
        )
        return [
            {"val": r["code"], "label": source_label(r["code"]), "count": r["count"]}
            for r in rows
        ]

    def _lemma_frequency_counts(self, af: dict) -> list[dict]:
        xf, params = self._lemma_where(af, "frequency")
        where = f"WHERE {xf}" if xf else ""
        rows = self.fetch_all(
            f"""
            SELECT bucket, count, sort_order FROM (
                SELECT
                    CASE
                        WHEN l.attestation_count > 500 THEN '500+'
                        WHEN l.attestation_count BETWEEN 101 AND 500 THEN '101-500'
                        WHEN l.attestation_count BETWEEN 11 AND 100 THEN '11-100'
                        WHEN l.attestation_count BETWEEN 2 AND 10 THEN '2-10'
                        WHEN l.attestation_count = 1 THEN '1'
                        ELSE '0'
                    END AS bucket,
                    CASE
                        WHEN l.attestation_count > 500 THEN 1
                        WHEN l.attestation_count BETWEEN 101 AND 500 THEN 2
                        WHEN l.attestation_count BETWEEN 11 AND 100 THEN 3
                        WHEN l.attestation_count BETWEEN 2 AND 10 THEN 4
                        WHEN l.attestation_count = 1 THEN 5
                        ELSE 6
                    END AS sort_order,
                    COUNT(*) AS count
                FROM lexical_lemmas l
                {where}
                GROUP BY bucket, sort_order
            ) sub
            ORDER BY sort_order
        """,
            params,
        )
        labels = {
            "500+": "Very Common (500+)",
            "101-500": "Common (101\u2013500)",
            "11-100": "Uncommon (11\u2013100)",
            "2-10": "Rare (2\u201310)",
            "1": "Hapax (1)",
            "0": "Unattested (0)",
        }
        return [
            {
                "val": r["bucket"],
                "label": labels.get(r["bucket"], r["bucket"]),
                "count": r["count"],
            }
            for r in rows
            if r["bucket"] != "0" or r["count"] > 0
        ]

    def _sign_language_counts(self, af: dict) -> list[dict]:
        # Signs have language_codes array; count per language
        rows = self.fetch_all("""
            SELECT lang, COUNT(*) AS count
            FROM lexical_signs, LATERAL unnest(language_codes) lang
            GROUP BY lang
            ORDER BY count DESC
        """)
        lm = self._lang_map()
        return [
            {
                "val": r["lang"],
                "label": lm.get(r["lang"], r["lang"]),
                "count": r["count"],
            }
            for r in rows
        ]

    def _sign_source_counts(self, af: dict) -> list[dict]:
        rows = self.fetch_all("""
            SELECT source AS code, COUNT(*) AS count
            FROM lexical_signs
            GROUP BY source
            ORDER BY count DESC
        """)
        return [
            {"val": r["code"], "label": source_label(r["code"]), "count": r["count"]}
            for r in rows
        ]

    def _meaning_language_counts(self, af: dict) -> list[dict]:
        xf, params = self._lemma_where(af, "language")
        extra = f"AND {xf}" if xf else ""
        rows = self.fetch_all(
            f"""
            SELECT
                CASE
                    WHEN l.language_code LIKE 'akk%%' THEN 'akk'
                    WHEN l.language_code LIKE 'sux%%' THEN 'sux'
                    ELSE l.language_code
                END AS code,
                COUNT(DISTINCT l.guide_word) AS count
            FROM lexical_lemmas l
            WHERE l.guide_word IS NOT NULL AND l.guide_word <> ''
            {extra}
            GROUP BY code
            HAVING COUNT(DISTINCT l.guide_word) > 0
            ORDER BY count DESC
        """,
            params,
        )
        lm = self._lang_map()
        return [
            {
                "val": r["code"],
                "label": lm.get(r["code"], r["code"]),
                "count": r["count"],
            }
            for r in rows
        ]

    def _meaning_pos_counts(self, af: dict) -> list[dict]:
        xf, params = self._lemma_where(af, "pos")
        extra = f"AND {xf}" if xf else ""
        rows = self.fetch_all(
            f"""
            SELECT l.pos AS code, COUNT(DISTINCT l.guide_word) AS count
            FROM lexical_lemmas l
            WHERE l.guide_word IS NOT NULL AND l.guide_word <> ''
              AND l.pos IS NOT NULL AND l.pos <> ''
            {extra}
            GROUP BY l.pos
            ORDER BY count DESC
        """,
            params,
        )
        return [
            {"val": r["code"], "label": pos_label(r["code"]), "count": r["count"]}
            for r in rows
        ]

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _freq_condition(bucket: str) -> str:
        if bucket == "1":
            return "l.attestation_count = 1"
        elif bucket == "2-10":
            return "l.attestation_count BETWEEN 2 AND 10"
        elif bucket == "11-100":
            return "l.attestation_count BETWEEN 11 AND 100"
        elif bucket == "101-500":
            return "l.attestation_count BETWEEN 101 AND 500"
        elif bucket == "500+":
            return "l.attestation_count > 500"
        return "TRUE"
