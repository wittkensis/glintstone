"""Artifact repository — search, detail, composites, images."""

import math
from collections import defaultdict

from core.repository import BaseRepository

# Column mappings for direct-column filter dimensions
# Genre and language use junction tables instead (handled separately)
_DIM_COLS = {
    "period": "a.period_normalized",
    "provenience": "a.provenience_normalized",
}


class ArtifactRepository(BaseRepository):
    # ── Filter options with grouped counts ──────────────────

    def _cross_filter_where(
        self, active: dict[str, list[str]], exclude: str
    ) -> tuple[str, dict]:
        """Build WHERE conditions for all dimensions except `exclude`.

        Used for cross-filter counts: each dimension's counts reflect
        the other dimensions' active filters but not its own.
        """
        conditions: list[str] = []
        params: dict = {}
        for dim, values in active.items():
            if dim == exclude or not values:
                continue
            if dim in _DIM_COLS:
                col = _DIM_COLS[dim]
                clause, p = self.build_in_clause(values, prefix=f"xf_{dim}")
                conditions.append(f"{col} {clause}")
                params.update(p)
            elif dim == "genre":
                clause, p = self.build_in_clause(values, prefix="xf_genre")
                conditions.append(f"""EXISTS (
                    SELECT 1 FROM artifact_genres ag
                    JOIN canonical_genres cg ON ag.genre_id = cg.id
                    WHERE ag.p_number = a.p_number AND cg.name {clause}
                )""")
                params.update(p)
            elif dim == "language":
                clause, p = self.build_in_clause(values, prefix="xf_lang")
                conditions.append(f"""EXISTS (
                    SELECT 1 FROM artifact_languages al
                    JOIN canonical_languages cl ON al.language_id = cl.id
                    WHERE al.p_number = a.p_number AND cl.name {clause}
                )""")
                params.update(p)
        return (" AND ".join(conditions), params) if conditions else ("", {})

    def get_filter_options(
        self, active_filters: dict[str, list[str]] | None = None
    ) -> dict:
        """Return filter options with counts, grouped for period/provenience.

        active_filters: currently-selected values per dimension.
        Counts are cross-filtered (each dimension excludes its own filter).
        """
        af = active_filters or {}
        options: dict = {}

        # Period — grouped by period_canon.group_name, with date ranges
        xf_where, xf_params = self._cross_filter_where(af, "period")
        artifact_filter = f"AND {xf_where}" if xf_where else ""
        rows = self.fetch_all(
            f"""
            SELECT pc.canonical AS val,
                   pc.group_name,
                   pc.sort_order,
                   pc.date_start_bce AS date_start,
                   pc.date_end_bce AS date_end,
                   COUNT(a.p_number) AS count
            FROM (
                SELECT DISTINCT ON (canonical)
                    canonical,
                    COALESCE(group_name, 'Other') AS group_name,
                    sort_order, date_start_bce, date_end_bce
                FROM period_canon
                ORDER BY canonical, sort_order NULLS LAST
            ) pc
            LEFT JOIN artifacts a
                ON a.period_normalized = pc.canonical
                {artifact_filter}
            GROUP BY pc.canonical, pc.group_name, pc.sort_order,
                     pc.date_start_bce, pc.date_end_bce
            HAVING COUNT(a.p_number) > 0
            ORDER BY pc.sort_order NULLS LAST, pc.canonical
        """,
            xf_params,
        )
        options["period"] = self._group_rows(
            rows, "group_name", extra_keys=("date_start", "date_end")
        )

        # Provenience — grouped by region > subregion
        # Deduplicate provenience_canon (multiple raw values per ancient_name)
        xf_where, xf_params = self._cross_filter_where(af, "provenience")
        artifact_filter = f"AND {xf_where}" if xf_where else ""
        rows = self.fetch_all(
            f"""
            SELECT pc.ancient_name AS val,
                   COALESCE(pc.region, 'Unknown') AS region,
                   pc.subregion,
                   pc.sort_order,
                   COUNT(a.p_number) AS count
            FROM (
                SELECT DISTINCT ON (ancient_name)
                    ancient_name, region, subregion, sort_order
                FROM provenience_canon
                ORDER BY ancient_name, sort_order NULLS LAST
            ) pc
            LEFT JOIN artifacts a
                ON a.provenience_normalized = pc.ancient_name
                {artifact_filter}
            GROUP BY pc.ancient_name, pc.region, pc.subregion, pc.sort_order
            HAVING COUNT(a.p_number) > 0
            ORDER BY pc.region, pc.subregion NULLS LAST, pc.sort_order NULLS LAST
        """,
            xf_params,
        )
        options["provenience"] = self._group_prov_rows(rows)

        # Genre — flat list via junction table
        xf_where, xf_params = self._cross_filter_where(af, "genre")
        where_clause = f"WHERE {xf_where}" if xf_where else ""
        rows = self.fetch_all(
            f"""
            SELECT cg.name AS val, COUNT(DISTINCT ag.p_number) AS count
            FROM canonical_genres cg
            JOIN artifact_genres ag ON ag.genre_id = cg.id
            JOIN artifacts a ON a.p_number = ag.p_number
            {where_clause}
            GROUP BY cg.name
            HAVING COUNT(DISTINCT ag.p_number) > 0
            ORDER BY count DESC
        """,
            xf_params,
        )
        options["genre"] = [{"val": r["val"], "count": r["count"]} for r in rows]

        # Language — flat list via junction table
        xf_where, xf_params = self._cross_filter_where(af, "language")
        where_clause = f"WHERE {xf_where}" if xf_where else ""
        rows = self.fetch_all(
            f"""
            SELECT cl.name AS val, COUNT(DISTINCT al.p_number) AS count
            FROM canonical_languages cl
            JOIN artifact_languages al ON al.language_id = cl.id
            JOIN artifacts a ON a.p_number = al.p_number
            {where_clause}
            GROUP BY cl.name
            HAVING COUNT(DISTINCT al.p_number) > 0
            ORDER BY count DESC
        """,
            xf_params,
        )
        options["language"] = [{"val": r["val"], "count": r["count"]} for r in rows]

        return options

    @staticmethod
    def _group_rows(
        rows: list[dict], group_key: str, extra_keys: tuple[str, ...] = ()
    ) -> list[dict]:
        """Group flat rows into [{group, total, children: [{val, count, ...}]}].

        Key is 'children' not 'items' to avoid collision with dict.items() in Jinja2.
        extra_keys are passed through from each row into the child dict.
        """
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            item: dict = {"val": r["val"], "count": r["count"]}
            for k in extra_keys:
                if r.get(k) is not None:
                    item[k] = r[k]
            groups[r[group_key]].append(item)
        return [
            {
                "group": name,
                "total": sum(v["count"] for v in vals),
                "children": vals,
            }
            for name, vals in groups.items()
        ]

    @staticmethod
    def _group_prov_rows(rows: list[dict]) -> list[dict]:
        """Group provenience rows by 'region > subregion' label."""
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            region = r["region"]
            subregion = r["subregion"]
            label = f"{region} ({subregion})" if subregion else region
            groups[label].append({"val": r["val"], "count": r["count"]})
        return [
            {
                "group": name,
                "total": sum(v["count"] for v in vals),
                "children": vals,
            }
            for name, vals in groups.items()
        ]

    # ── Search with multi-select ────────────────────────────

    def search(
        self,
        search: str | None = None,
        pipeline: str | None = None,
        period: list[str] | None = None,
        provenience: list[str] | None = None,
        genre: list[str] | None = None,
        language: list[str] | None = None,
        has_ocr: bool = False,
        page: int = 1,
        per_page: int = 24,
    ) -> dict:
        conditions: list[str] = []
        params: dict = {}

        if search:
            # Support || for OR search
            terms = [t.strip() for t in search.split("||") if t.strip()]
            if terms:
                search_conds = []
                for i, term in enumerate(terms):
                    key = f"search{i}"
                    search_conds.append(
                        f"(a.p_number ILIKE %({key})s OR a.designation ILIKE %({key})s)"
                    )
                    params[key] = f"%{term}%"
                conditions.append(f"({' OR '.join(search_conds)})")

        if pipeline == "needs_reading":
            conditions.append(
                "(ps.reading_complete IS NULL OR ps.reading_complete < 0.5)"
            )
        elif pipeline == "needs_linguistic":
            conditions.append(
                "(ps.reading_complete > 0 AND (ps.linguistic_complete IS NULL OR ps.linguistic_complete < 0.5))"
            )
        elif pipeline == "complete":
            conditions.append("(ps.semantic_complete >= 1.0)")

        if period:
            clause, p = self.build_in_clause(period, prefix="period")
            conditions.append(f"a.period_normalized {clause}")
            params.update(p)
        if provenience:
            clause, p = self.build_in_clause(provenience, prefix="prov")
            conditions.append(f"a.provenience_normalized {clause}")
            params.update(p)
        if genre:
            clause, p = self.build_in_clause(genre, prefix="genre")
            conditions.append(f"""EXISTS (
                SELECT 1 FROM artifact_genres ag
                JOIN canonical_genres cg ON ag.genre_id = cg.id
                WHERE ag.p_number = a.p_number AND cg.name {clause}
            )""")
            params.update(p)
        if language:
            clause, p = self.build_in_clause(language, prefix="lang")
            conditions.append(f"""EXISTS (
                SELECT 1 FROM artifact_languages al
                JOIN canonical_languages cl ON al.language_id = cl.id
                WHERE al.p_number = a.p_number AND cl.name {clause}
            )""")
            params.update(p)
        if has_ocr:
            conditions.append("ps.graphemic_complete > 0")

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * per_page
        params["per_page"] = per_page
        params["offset"] = offset

        items = self.fetch_all(
            f"""
            SELECT a.p_number, a.designation,
                   COALESCE(a.language_normalized, a.language) as language,
                   COALESCE(a.period_normalized, a.period) as period,
                   COALESCE(a.provenience_normalized, a.provenience) as provenience,
                   a.genre,
                   ps.physical_complete, ps.graphemic_complete,
                   ps.reading_complete, ps.linguistic_complete,
                   ps.semantic_complete, ps.has_image
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            {where}
            ORDER BY a.p_number
            LIMIT %(per_page)s OFFSET %(offset)s
        """,
            params,
        )

        # Count query (same conditions, no LIMIT)
        count_params = {
            k: v for k, v in params.items() if k not in ("per_page", "offset")
        }
        total = self.fetch_scalar(
            f"""
            SELECT COUNT(*)
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            {where}
        """,
            count_params,
        )

        total = total or 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page) if per_page else 0,
        }

    def find_by_p_number(self, p_number: str) -> dict | None:
        artifact = self.fetch_one(
            """
            SELECT a.*, ps.physical_complete, ps.graphemic_complete,
                   ps.reading_complete, ps.linguistic_complete,
                   ps.semantic_complete, ps.has_image, ps.has_atf,
                   ps.has_lemmas, ps.has_translation, ps.has_sign_annotations,
                   ps.quality_score
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE a.p_number = %(p_number)s
        """,
            {"p_number": p_number},
        )

        if not artifact:
            return None

        # Attach composites
        artifact["composites"] = self.get_composites(p_number)

        # Attach images
        artifact["images"] = self.get_images(p_number)

        # Attach ORACC credits
        artifact["oracc_credits"] = self.get_oracc_credits(p_number)

        # Nullify CDLI placeholder attribution values
        _placeholders = {"no atf", "no translation", "check", "uncertain", "nn"}
        for field in ("atf_source", "translation_source", "publication_author"):
            val = artifact.get(field)
            if val and val.strip().lower() in _placeholders:
                artifact[field] = None

        # Build pipeline dict (short keys for template macro)
        artifact["pipeline"] = {
            "physical": artifact.get("physical_complete"),
            "reading": artifact.get("reading_complete"),
            "linguistic": artifact.get("linguistic_complete"),
            "semantic": artifact.get("semantic_complete"),
        }

        return artifact

    def get_composites(self, p_number: str) -> list[dict]:
        return self.fetch_all(
            """
            SELECT c.q_number, c.designation, c.language, c.period,
                   c.genre, c.exemplar_count
            FROM composites c
            JOIN artifact_composites ac ON c.q_number = ac.q_number
            WHERE ac.p_number = %(p_number)s
        """,
            {"p_number": p_number},
        )

    def get_composite_tablets(self, q_number: str) -> list[dict]:
        return self.fetch_all(
            """
            SELECT a.p_number, a.designation, a.period, ps.has_image, ac.line_ref
            FROM artifact_composites ac
            JOIN artifacts a ON ac.p_number = a.p_number
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE ac.q_number = %(q_number)s
            ORDER BY a.p_number
        """,
            {"q_number": q_number},
        )

    def get_images(self, p_number: str) -> list[dict]:
        return self.fetch_all(
            """
            SELECT s.surface_type, si.image_path, si.is_primary, si.image_type
            FROM surfaces s
            JOIN surface_images si ON s.id = si.surface_id
            WHERE s.p_number = %(p_number)s
            ORDER BY si.is_primary DESC
        """,
            {"p_number": p_number},
        )

    def get_oracc_credits(self, p_number: str) -> list[dict]:
        return self.fetch_all(
            """
            SELECT oracc_project, credits_text
            FROM artifact_credits
            WHERE p_number = %(p_number)s
            ORDER BY oracc_project
        """,
            {"p_number": p_number},
        )

    def get_atf(self, p_number: str) -> dict:
        """Get ATF text lines for a tablet."""
        lines = self.fetch_all(
            """
            SELECT
                tl.line_number,
                tl.raw_atf,
                tl.is_ruling,
                tl.is_blank,
                s.surface_type,
                tl.column_number
            FROM text_lines tl
            LEFT JOIN surfaces s ON tl.surface_id = s.id
            WHERE tl.p_number = %(p_number)s
            ORDER BY tl.column_number, tl.id
        """,
            {"p_number": p_number},
        )

        return {"p_number": p_number, "lines": lines, "total_lines": len(lines)}

    def _translation_rows(
        self,
        p_number: str,
        lang_filter: str | None = None,
        lang_exclude: str | None = None,
    ) -> list[dict]:
        """Fetch translation rows with optional language filter/exclude."""
        clauses = ["t.p_number = %(p_number)s"]
        params: dict = {"p_number": p_number}
        if lang_filter:
            clauses.append("t.language = %(lang)s")
            params["lang"] = lang_filter
        elif lang_exclude:
            clauses.append("t.language != %(lang)s")
            params["lang"] = lang_exclude
        where = " AND ".join(clauses)
        return self.fetch_all(
            f"""
            SELECT t.id, t.line_id, tl.line_number, s.surface_type,
                   tl.column_number, t.translation, t.language, t.source
            FROM translations t
            LEFT JOIN text_lines tl ON t.line_id = tl.id
            LEFT JOIN surfaces s ON tl.surface_id = s.id
            WHERE {where}
            ORDER BY t.id
            """,
            params,
        )

    @staticmethod
    def _group_translation_rows(rows: list[dict]) -> dict:
        """Split rows into matched (keyed by surface_col_linenum) and unmatched."""
        matched: dict[str, dict] = {}
        unmatched: list[dict] = []
        for r in rows:
            if r["line_id"] and r["line_number"]:
                surface = r["surface_type"] or "obverse"
                col = r["column_number"] or 1
                key = f"{surface}_{col}_{r['line_number']}"
                matched[key] = {"text": r["translation"]}
            else:
                unmatched.append({"text": r["translation"], "id": r["id"]})
        return {"matched": matched, "unmatched": unmatched}

    def get_translation(self, p_number: str) -> dict:
        """Get translation data grouped by language (excludes ts).

        Returns:
        {
            has_translation, languages: [...],
            translations: {lang: {matched: {...}, unmatched: [...]}}
        }
        """
        rows = self._translation_rows(p_number, lang_exclude="ts")
        if not rows:
            return {
                "has_translation": False,
                "languages": [],
                "translations": {},
            }

        by_lang: dict[str, list[dict]] = {}
        for r in rows:
            by_lang.setdefault(r["language"] or "en", []).append(r)

        translations = {
            lang: self._group_translation_rows(lang_rows)
            for lang, lang_rows in by_lang.items()
        }

        lang_order = sorted(translations.keys(), key=lambda lang: (lang != "en", lang))

        return {
            "has_translation": True,
            "languages": lang_order,
            "translations": translations,
        }

    def get_normalized(self, p_number: str) -> dict:
        """Get normalized readings (ts language) as a separate scholarly layer.

        Returns:
        { has_normalized, matched: {surface_col_linenum: {text}}, unmatched: [...] }
        """
        rows = self._translation_rows(p_number, lang_filter="ts")
        if not rows:
            return {"has_normalized": False, "matched": {}, "unmatched": []}

        grouped = self._group_translation_rows(rows)
        return {"has_normalized": True, **grouped}

    def get_lemmas(self, p_number: str) -> dict:
        """Get lemmatization data for a tablet, including per-word language."""
        lemmas = self.fetch_all(
            """
            SELECT
                tl.line_number,
                t.position,
                t.gdl_json,
                t.lang AS token_lang,
                l.citation_form,
                l.guide_word,
                l.sense,
                l.pos,
                l.epos,
                l.norm,
                l.base,
                l.language AS word_language
            FROM lemmatizations l
            JOIN tokens t ON l.token_id = t.id
            JOIN text_lines tl ON t.line_id = tl.id
            WHERE tl.p_number = %(p_number)s
            ORDER BY tl.line_number, t.position
        """,
            {"p_number": p_number},
        )

        return {"p_number": p_number, "lemmas": lemmas, "total": len(lemmas)}

    def debug_all(self, p_number: str) -> dict | None:
        """Aggregate every data layer for a single artifact."""
        artifact = self.find_by_p_number(p_number)
        if not artifact:
            return None

        def _safe_query(sql: str, params: dict) -> list[dict] | str:
            """Run a query, returning error string if the table doesn't exist."""
            try:
                return self.fetch_all(sql, params)
            except Exception as e:
                # Roll back so the connection stays usable
                self.conn.rollback()
                return f"[query error: {e}]"

        params = {"p_number": p_number}

        surfaces = _safe_query(
            """
            SELECT s.id, s.surface_type, s.surface_preservation
            FROM surfaces s
            WHERE s.p_number = %(p_number)s
            ORDER BY s.id
        """,
            params,
        )

        tokens = _safe_query(
            """
            SELECT t.id, t.line_id, tl.line_number, t.position,
                   t.gdl_json, t.lang
            FROM tokens t
            JOIN text_lines tl ON t.line_id = tl.id
            WHERE tl.p_number = %(p_number)s
            ORDER BY tl.line_number, t.position
        """,
            params,
        )

        identifiers = _safe_query(
            """
            SELECT identifier_type, identifier_value, authority
            FROM artifact_identifiers
            WHERE p_number = %(p_number)s
        """,
            params,
        )

        sign_annotations = _safe_query(
            """
            SELECT sa.sign_id, sa.bbox_x, sa.bbox_y, sa.bbox_w, sa.bbox_h,
                   sa.confidence, sa.annotation_run_id
            FROM sign_annotations sa
            JOIN surface_images si ON sa.surface_image_id = si.id
            JOIN surfaces s ON si.surface_id = s.id
            WHERE s.p_number = %(p_number)s
            ORDER BY sa.bbox_y, sa.bbox_x
        """,
            params,
        )

        return {
            "artifact": artifact,
            "atf": self.get_atf(p_number),
            "translation": self.get_translation(p_number),
            "lemmas": self.get_lemmas(p_number),
            "surfaces": surfaces,
            "tokens": tokens,
            "identifiers": identifiers,
            "sign_annotations": sign_annotations,
        }

    # ── Sign annotations (OCR overlay) ───────────────────────

    def get_sign_annotations(self, p_number: str) -> dict:
        """Return sign annotations for the overlay viewer."""
        rows = self.fetch_all(
            """
            SELECT sa.sign_id, sa.bbox_x, sa.bbox_y, sa.bbox_w, sa.bbox_h,
                   sa.confidence, s.surface_type
            FROM sign_annotations sa
            JOIN surface_images si ON sa.surface_image_id = si.id
            JOIN surfaces s ON si.surface_id = s.id
            WHERE s.p_number = %(p_number)s
            ORDER BY sa.bbox_y, sa.bbox_x
            """,
            {"p_number": p_number},
        )
        return {"annotations": rows, "count": len(rows)}

    # ── Research data (publications, scholars, storage) ────

    def get_research(self, p_number: str) -> dict:
        """Return all publication/citation data for the Research sidebar tab."""

        # Storage location
        storage = self.fetch_one(
            "SELECT museum_no, collection FROM artifacts WHERE p_number = %(p)s",
            {"p": p_number},
        )

        # Editions joined with publications
        editions = self.fetch_all(
            """
            SELECT ae.id AS edition_id, ae.edition_type, ae.reference_string,
                   ae.is_current_edition, ae.note,
                   p.id AS publication_id, p.title, p.short_title, p.year,
                   p.authors, p.doi, p.cited_by_count, p.publication_type,
                   p.url, p.bibtex_key
            FROM artifact_editions ae
            JOIN publications p ON ae.publication_id = p.id
            WHERE ae.p_number = %(p)s
            ORDER BY ae.is_current_edition DESC, p.year DESC NULLS LAST
            """,
            {"p": p_number},
        )

        # Scholars aggregated across all editions for this tablet
        scholars = self.fetch_all(
            """
            SELECT s.id, s.name, s.orcid, s.institution, pa.role,
                   count(DISTINCT ae.publication_id) AS pub_count
            FROM artifact_editions ae
            JOIN publication_authors pa ON ae.publication_id = pa.publication_id
            JOIN scholars s ON pa.scholar_id = s.id
            WHERE ae.p_number = %(p)s
              AND s.name != 'Unknown'
              AND s.author_type = 'person'
            GROUP BY s.id, s.name, s.orcid, s.institution, pa.role
            ORDER BY pub_count DESC, s.name
            """,
            {"p": p_number},
        )

        # Group editions by type
        grouped: dict[str, list] = {}
        for ed in editions:
            grouped.setdefault(ed["edition_type"], []).append(ed)

        return {
            "storage": storage or {},
            "scholars": scholars,
            "editions": editions,
            "editions_by_type": grouped,
            "total_editions": len(editions),
        }
