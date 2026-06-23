"""Artifact repository — search, detail, composites, images."""

import math
import os
import time
from collections import defaultdict

from core.repository import BaseRepository

# Column mappings for direct-column filter dimensions
# Genre and language use junction tables instead (handled separately)
_DIM_COLS = {
    "period": "a.period_normalized",
    "provenience": "a.provenience_normalized",
}

# ── Filter-options TTL cache ────────────────────────────────────────────────
# Filter counts only change when ingestion runs, not per-request. A short TTL
# eliminates the four serial SQL queries for the vast majority of traffic.
# Override the TTL with FILTER_OPTIONS_CACHE_TTL (seconds, 0 disables).
_FILTER_CACHE: dict = {}
_FILTER_CACHE_TTL = float(os.environ.get("FILTER_OPTIONS_CACHE_TTL", "60"))


def _filter_cache_key(active_filters: dict[str, list[str]]) -> tuple:
    return tuple(sorted((k, tuple(sorted(v))) for k, v in active_filters.items()))


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

    def _get_filter_options_from_view(self) -> dict | None:
        """Read unfiltered filter counts from the filter_options_cache materialized view.

        Returns a dict keyed by dimension if the view exists, or None if it
        hasn't been created yet (migration 042 not yet applied). The caller
        falls back to the four-query path on None.

        The view stores flat (dimension, value, count) rows — not the
        grouped structures that get_filter_options returns. Grouping by
        group_name / region requires period_canon and provenience_canon
        metadata that isn't in the view, so for simplicity the unfiltered
        fast path returns flat lists (consistent with the filtered path for
        genre/language). Period and provenience grouping is a UI convenience
        that the web layer can apply client-side using the existing period_canon
        and provenience_canon API endpoints.
        """
        try:
            rows = self.fetch_all(
                "SELECT dimension, value, count FROM filter_options_cache ORDER BY dimension, count DESC",
                {},
            )
        except Exception:
            # View doesn't exist yet — migration 042 not applied.
            return None

        result: dict[str, list[dict]] = {
            "period": [],
            "provenience": [],
            "genre": [],
            "language": [],
        }
        for row in rows:
            dim = row["dimension"]
            if dim in result:
                result[dim].append({"val": row["value"], "count": row["count"]})
        return result

    def get_filter_options(
        self, active_filters: dict[str, list[str]] | None = None
    ) -> dict:
        """Return filter options with counts, grouped for period/provenience.

        active_filters: currently-selected values per dimension.
        Counts are cross-filtered (each dimension excludes its own filter).

        Implementation note: this runs four sequential SQL queries. A single
        CTE doesn't easily share work across dimensions because each dimension
        uses a different WHERE (cross-filter excludes self). The TTL cache
        above already collapses repeated calls — for cold cache, the four
        queries hit a warm Postgres pool on the same host with negligible
        per-query connection overhead. See issue #83 phase 4d for the
        deferred psycopg3 pipeline-mode variant if profiling later shows the
        cold path is a bottleneck.
        """
        af = active_filters or {}

        if _FILTER_CACHE_TTL > 0:
            key = _filter_cache_key(af)
            cached = _FILTER_CACHE.get(key)
            if cached is not None:
                payload, ts = cached
                if time.monotonic() - ts < _FILTER_CACHE_TTL:
                    return payload

        # Fast path: read from the filter_options_cache materialized view when
        # no cross-filters are active (the view holds unfiltered counts only).
        # Falls back to the four-query path when the view doesn't exist yet
        # (i.e. migration 042 hasn't run) or when active filters require
        # per-dimension cross-filtering.
        if not af:
            cached_options = self._get_filter_options_from_view()
            if cached_options is not None:
                if _FILTER_CACHE_TTL > 0:
                    _FILTER_CACHE[_filter_cache_key(af)] = (
                        cached_options,
                        time.monotonic(),
                    )
                return cached_options
            # View unavailable — fall through to the full query path below.

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

        # Genre — flat list via junction table. COUNT(*) is safe here:
        # artifact_genres has PRIMARY KEY (p_number, genre_id), so within a single
        # genre group there's at most one row per p_number — DISTINCT is redundant
        # and forces an extra dedup pass.
        xf_where, xf_params = self._cross_filter_where(af, "genre")
        where_clause = f"WHERE {xf_where}" if xf_where else ""
        rows = self.fetch_all(
            f"""
            SELECT cg.name AS val, COUNT(*) AS count
            FROM canonical_genres cg
            JOIN artifact_genres ag ON ag.genre_id = cg.id
            JOIN artifacts a ON a.p_number = ag.p_number
            {where_clause}
            GROUP BY cg.name
            HAVING COUNT(*) > 0
            ORDER BY count DESC
        """,
            xf_params,
        )
        options["genre"] = [{"val": r["val"], "count": r["count"]} for r in rows]

        # Language — same reasoning as genre. artifact_languages has
        # PRIMARY KEY (p_number, language_id) so COUNT(*) is equivalent to
        # COUNT(DISTINCT p_number) within each group.
        xf_where, xf_params = self._cross_filter_where(af, "language")
        where_clause = f"WHERE {xf_where}" if xf_where else ""
        rows = self.fetch_all(
            f"""
            SELECT cl.name AS val, COUNT(*) AS count
            FROM canonical_languages cl
            JOIN artifact_languages al ON al.language_id = cl.id
            JOIN artifacts a ON a.p_number = al.p_number
            {where_clause}
            GROUP BY cl.name
            HAVING COUNT(*) > 0
            ORDER BY count DESC
        """,
            xf_params,
        )
        options["language"] = [{"val": r["val"], "count": r["count"]} for r in rows]

        if _FILTER_CACHE_TTL > 0:
            _FILTER_CACHE[_filter_cache_key(af)] = (options, time.monotonic())

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

        # LATERAL pick of the primary cached image so cards can show a real
        # thumbnail when artifact_images has one. ORDER prefers display_order
        # 0 (the canonical primary), then photo over lineart, then row id.
        #
        # COUNT(*) OVER() returns the total matching rows pre-LIMIT, so we get
        # the total alongside the page in a single round trip instead of running
        # a second COUNT query.
        items = self.fetch_all(
            f"""
            SELECT a.p_number, a.designation,
                   COALESCE(a.language_normalized, a.language) as language,
                   COALESCE(a.period_normalized, a.period) as period,
                   COALESCE(a.provenience_normalized, a.provenience) as provenience,
                   a.genre,
                   ps.physical_complete, ps.graphemic_complete,
                   ps.reading_complete, ps.linguistic_complete,
                   ps.semantic_complete, ps.has_image,
                   primary_img.r2_thumbnail_key AS primary_thumbnail_key,
                   primary_img.credit_line     AS primary_credit_line,
                   COUNT(*) OVER() AS _total_count
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            LEFT JOIN LATERAL (
                SELECT ai.r2_thumbnail_key, ai.credit_line
                FROM artifact_images ai
                WHERE ai.p_number = a.p_number
                ORDER BY ai.display_order,
                         (ai.image_type = 'photo') DESC,
                         ai.id
                LIMIT 1
            ) primary_img ON true
            {where}
            ORDER BY a.p_number
            LIMIT %(per_page)s OFFSET %(offset)s
        """,
            params,
        )

        if items:
            total = items[0].get("_total_count") or 0
            for row in items:
                row.pop("_total_count", None)
        else:
            # Empty result set: could be a real no-match OR an out-of-range
            # page request. Run a dedicated count to distinguish so pagination
            # still shows the right total when the user overshoots.
            count_params = {
                k: v for k, v in params.items() if k not in ("per_page", "offset")
            }
            total = (
                self.fetch_scalar(
                    f"""
                SELECT COUNT(*)
                FROM artifacts a
                LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
                {where}
            """,
                    count_params,
                )
                or 0
            )
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

        # Attach a confident Wikidata link for the provenience (place), if one
        # exists. Issue #281 surfaces the #164 entity_wikidata_links data: the
        # artifact's normalized place name → provenience_canon.pleiades_id →
        # entity_wikidata_links. Only high-confidence, ID-based (pleiades) place
        # links are shown; a missing/ambiguous match yields no link (no empty UI).
        artifact["provenience_wikidata_qid"] = self.get_provenience_wikidata_qid(
            artifact.get("provenience_normalized")
        )

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

    def get_provenience_wikidata_qid(
        self, provenience_normalized: str | None
    ) -> str | None:
        """Return the confident Wikidata Q-number for a normalized place name.

        Join path (Issue #281, data from #164):
            provenience_canon.ancient_name (= artifacts.provenience_normalized)
              → provenience_canon.pleiades_id
              → entity_wikidata_links.source_key  (entity_type='place',
                                                    match_basis='pleiades')

        Only ID-based place links are returned (the only confident basis shipped).
        Returns None when there is no confident match — the caller renders nothing.
        """
        if not provenience_normalized:
            return None
        row = self.fetch_one(
            """
            SELECT ewl.wikidata_qid
            FROM provenience_canon pc
            JOIN entity_wikidata_links ewl
              ON ewl.source_key = pc.pleiades_id
             AND ewl.entity_type = 'place'
             AND ewl.match_basis = 'pleiades'
            WHERE pc.ancient_name = %(name)s
              AND pc.pleiades_id IS NOT NULL
            LIMIT 1
        """,
            {"name": provenience_normalized},
        )
        return row["wikidata_qid"] if row else None

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

    def get_artifact_image_records(self, p_number: str) -> list[dict]:
        """Rows from the artifact_images table (migration 022).

        Distinct from get_images() above, which reads the legacy surface_images
        table. The new artifact_images table holds R2-backed image metadata
        with per-image copyright/attribution. Routes turn each row into a
        public URL via core.storage.public_url_for_key.
        """
        return self.fetch_all(
            """
            SELECT id, image_type, cdli_reader_id, r2_key, r2_thumbnail_key,
                   mime_type, byte_size, width, height,
                   copyright_holder, license, attribution_raw, credit_line,
                   display_order, ingested_at
            FROM artifact_images
            WHERE p_number = %(p_number)s
            ORDER BY display_order, image_type, id
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

    def get_competing_lemmas(self, p_number: str) -> dict:
        """Find tokens where multiple annotation runs assigned different citation forms.

        Returns a nested dict keyed by {line_index: {word_position: [readings]}},
        mirroring the structure used by get_lemmas so the ATF viewer can look
        up both datasets with the same (line_no, word_no) key.

        A token is only flagged as contested when at least two distinct
        citation_form values appear across its lemmatizations — differing
        annotation_run_ids on the same citation form is NOT a conflict.
        """
        rows = self.fetch_all(
            """
            SELECT
                tl.line_number,
                t.position,
                l.citation_form,
                l.guide_word,
                l.confidence,
                ar.source_type,
                ar.source_name
            FROM lemmatizations l
            JOIN tokens t ON l.token_id = t.id
            JOIN text_lines tl ON t.line_id = tl.id
            LEFT JOIN annotation_runs ar ON l.annotation_run_id = ar.id
            WHERE tl.p_number = %(p_number)s
              AND t.id IN (
                  -- Only tokens with 2+ distinct citation forms across all their lemmatizations
                  SELECT lz.token_id
                  FROM lemmatizations lz
                  JOIN tokens tk ON lz.token_id = tk.id
                  JOIN text_lines tl2 ON tk.line_id = tl2.id
                  WHERE tl2.p_number = %(p_number)s
                  GROUP BY lz.token_id
                  HAVING COUNT(DISTINCT lz.citation_form) > 1
              )
            ORDER BY tl.line_number, t.position, l.citation_form
            """,
            {"p_number": p_number},
        )

        # Build {line_idx: {position: [reading, ...]}} from flat rows
        grouped: dict[str, dict[str, list[dict]]] = {}
        for row in rows:
            ln = row.get("line_number", "")
            try:
                line_idx = int(str(ln).replace("'", "").rstrip(".")) - 1
            except (ValueError, TypeError):
                continue
            pos = row.get("position", 0)
            line_key = str(line_idx)
            word_key = str(pos)

            grouped.setdefault(line_key, {}).setdefault(word_key, []).append(
                {
                    "citation_form": row.get("citation_form"),
                    "guide_word": row.get("guide_word"),
                    "confidence": row.get("confidence"),
                    "source_type": row.get("source_type"),
                    "source": row.get("source_name"),
                }
            )

        # Deduplicate: keep only positions that still have 2+ distinct citation forms
        # after collapsing duplicate (citation_form, source) pairs.
        result: dict[str, dict[str, list[dict]]] = {}
        for line_key, positions in grouped.items():
            for word_key, readings in positions.items():
                seen_forms: set[str] = set()
                unique: list[dict] = []
                for r in readings:
                    cf = r.get("citation_form") or ""
                    if cf not in seen_forms:
                        seen_forms.add(cf)
                        unique.append(r)
                if len(unique) > 1:
                    result.setdefault(line_key, {})[word_key] = unique

        return {"p_number": p_number, "competing": result}

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
            SELECT sa.sign_id, sa.token_id, sa.bbox_x, sa.bbox_y, sa.bbox_w, sa.bbox_h,
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
