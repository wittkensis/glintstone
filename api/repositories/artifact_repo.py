"""Artifact repository — search, detail, composites, images."""

import math

from core.repository import BaseRepository


class ArtifactRepository(BaseRepository):
    def get_filter_options(self) -> dict:
        """Return sorted distinct values for each filterable field."""
        options = {}
        for col, alias in [
            ("period_normalized", "period"),
            ("provenience_normalized", "provenience"),
            ("genre", "genre"),
            ("COALESCE(language_normalized, language)", "language"),
        ]:
            rows = self.fetch_all(
                f"SELECT DISTINCT {col} AS val FROM artifacts WHERE {col} IS NOT NULL ORDER BY 1"
            )
            options[alias] = [r["val"] for r in rows]
        return options

    def search(
        self,
        search: str | None = None,
        pipeline: str | None = None,
        period: str | None = None,
        provenience: str | None = None,
        genre: str | None = None,
        language: str | None = None,
        has_ocr: bool = False,
        page: int = 1,
        per_page: int = 24,
    ) -> dict:
        conditions = []
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
            conditions.append("a.period_normalized = %(period)s")
            params["period"] = period
        if provenience:
            conditions.append("a.provenience_normalized = %(provenience)s")
            params["provenience"] = provenience
        if genre:
            conditions.append("a.genre = %(genre)s")
            params["genre"] = genre
        if language:
            conditions.append(
                "COALESCE(a.language_normalized, a.language) = %(language)s"
            )
            params["language"] = language
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

    def get_translation(self, p_number: str) -> dict:
        """Get translation data for a tablet.

        Returns the shape the ATF viewer expects:
        { has_translation, lines: {surface_col_linenum: {text}}, raw, language }
        """
        rows = self.fetch_all(
            """
            SELECT
                t.id,
                t.line_id,
                tl.line_number,
                s.surface_type,
                tl.column_number,
                t.translation,
                t.language,
                t.source
            FROM translations t
            LEFT JOIN text_lines tl ON t.line_id = tl.id
            LEFT JOIN surfaces s ON tl.surface_id = s.id
            WHERE t.p_number = %(p_number)s
            ORDER BY t.id
        """,
            {"p_number": p_number},
        )

        if not rows:
            return {"has_translation": False, "lines": {}, "raw": "", "language": None}

        language = rows[0]["language"] or "en"

        # Line-matched dict keyed by "surface_col_linenum"
        lines = {}
        for r in rows:
            if r["line_id"] and r["line_number"]:
                surface = r["surface_type"] or "obverse"
                col = r["column_number"] or 1
                key = f"{surface}_{col}_{r['line_number']}"
                lines[key] = {"text": r["translation"]}

        # Block text fallback
        raw = "\n".join(r["translation"] for r in rows if r["translation"])

        return {
            "has_translation": True,
            "lines": lines,
            "raw": raw,
            "language": language,
        }

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
