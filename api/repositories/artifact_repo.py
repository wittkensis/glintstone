"""Artifact repository — search, detail, composites, images."""

import math

from core.repository import BaseRepository


class ArtifactRepository(BaseRepository):

    def search(
        self,
        search: str | None = None,
        pipeline: str | None = None,
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

        if pipeline == "needs_graphemic":
            conditions.append(
                "(ps.has_image = 1 AND (ps.graphemic_complete IS NULL OR ps.graphemic_complete < 0.5))"
            )
        elif pipeline == "needs_reading":
            conditions.append(
                "(ps.reading_complete IS NULL OR ps.reading_complete < 0.5)"
            )
        elif pipeline == "needs_linguistic":
            conditions.append(
                "(ps.reading_complete > 0 AND (ps.linguistic_complete IS NULL OR ps.linguistic_complete < 0.5))"
            )
        elif pipeline == "complete":
            conditions.append(
                "(ps.reading_complete >= 1.0 AND ps.linguistic_complete >= 1.0)"
            )

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * per_page
        params["per_page"] = per_page
        params["offset"] = offset

        items = self.fetch_all(f"""
            SELECT a.p_number, a.designation, a.language, a.period,
                   a.provenience, a.genre,
                   ps.physical_complete, ps.graphemic_complete,
                   ps.reading_complete, ps.linguistic_complete,
                   ps.semantic_complete, ps.has_image
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            {where}
            ORDER BY a.p_number
            LIMIT %(per_page)s OFFSET %(offset)s
        """, params)

        # Count query (same conditions, no LIMIT)
        count_params = {k: v for k, v in params.items() if k not in ("per_page", "offset")}
        total = self.fetch_scalar(f"""
            SELECT COUNT(*)
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            {where}
        """, count_params)

        total = total or 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page) if per_page else 0,
        }

    def find_by_p_number(self, p_number: str) -> dict | None:
        artifact = self.fetch_one("""
            SELECT a.*, ps.physical_complete, ps.graphemic_complete,
                   ps.reading_complete, ps.linguistic_complete,
                   ps.semantic_complete, ps.has_image, ps.has_atf,
                   ps.has_lemmas, ps.has_translation, ps.has_sign_annotations,
                   ps.quality_score
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE a.p_number = %(p_number)s
        """, {"p_number": p_number})

        if not artifact:
            return None

        # Attach composites
        artifact["composites"] = self.get_composites(p_number)

        # Attach images
        artifact["images"] = self.get_images(p_number)

        # Build pipeline dict (short keys for template macro)
        artifact["pipeline"] = {
            "physical": artifact.get("physical_complete"),
            "graphemic": artifact.get("graphemic_complete"),
            "reading": artifact.get("reading_complete"),
            "linguistic": artifact.get("linguistic_complete"),
            "semantic": artifact.get("semantic_complete"),
        }

        return artifact

    def get_composites(self, p_number: str) -> list[dict]:
        return self.fetch_all("""
            SELECT c.q_number, c.designation, c.language, c.period,
                   c.genre, c.exemplar_count
            FROM composites c
            JOIN artifact_composites ac ON c.q_number = ac.q_number
            WHERE ac.p_number = %(p_number)s
        """, {"p_number": p_number})

    def get_composite_tablets(self, q_number: str) -> list[dict]:
        return self.fetch_all("""
            SELECT a.p_number, a.designation, a.period, ps.has_image, ac.line_ref
            FROM artifact_composites ac
            JOIN artifacts a ON ac.p_number = a.p_number
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE ac.q_number = %(q_number)s
            ORDER BY a.p_number
        """, {"q_number": q_number})

    def get_images(self, p_number: str) -> list[dict]:
        return self.fetch_all("""
            SELECT s.surface_type, si.image_path, si.is_primary, si.image_type
            FROM surfaces s
            JOIN surface_images si ON s.id = si.surface_id
            WHERE s.p_number = %(p_number)s
            ORDER BY si.is_primary DESC
        """, {"p_number": p_number})
