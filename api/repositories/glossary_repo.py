"""Glossary repository — browse, search, detail, counts."""

import math

from core.repository import BaseRepository


class GlossaryRepository(BaseRepository):
    def browse(
        self,
        search: str | None = None,
        group_type: str | None = None,
        group_value: str | None = None,
        sort_by: str = "frequency",
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        """Browse glossary entries with filtering and pagination."""
        conditions = []
        params: dict = {}

        # Search across multiple fields
        if search:
            search_term = f"%{search}%"
            conditions.append(
                """(headword ILIKE %(search)s
                    OR citation_form ILIKE %(search)s
                    OR guide_word ILIKE %(search)s
                    OR normalized_headword ILIKE %(search)s)"""
            )
            params["search"] = search_term

        # Group filtering
        if group_type and group_value:
            if group_type == "pos":
                # Exact match on POS
                conditions.append("pos = %(group_value)s")
                params["group_value"] = group_value

            elif group_type == "language":
                # Language family matching (akk includes akk-x-stdbab, etc.)
                conditions.append(
                    "(language = %(group_value)s OR language LIKE %(lang_family)s)"
                )
                params["group_value"] = group_value
                params["lang_family"] = f"{group_value}-%"

            elif group_type == "frequency":
                # Frequency bucket ranges
                if group_value == "1":
                    conditions.append("icount = 1")
                elif group_value == "2-10":
                    conditions.append("icount BETWEEN 2 AND 10")
                elif group_value == "11-100":
                    conditions.append("icount BETWEEN 11 AND 100")
                elif group_value == "101-500":
                    conditions.append("icount BETWEEN 101 AND 500")
                elif group_value == "500+":
                    conditions.append("icount > 500")

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Sorting
        if sort_by == "alpha":
            order = "ORDER BY citation_form ASC, headword ASC"
        else:  # frequency (default)
            order = "ORDER BY icount DESC, citation_form ASC"

        offset = (page - 1) * per_page
        params["per_page"] = per_page
        params["offset"] = offset

        # Fetch items
        items = self.fetch_all(
            f"""
            SELECT entry_id, headword, citation_form, guide_word,
                   language, pos, icount
            FROM glossary_entries
            {where}
            {order}
            LIMIT %(per_page)s OFFSET %(offset)s
        """,
            params,
        )

        # Count total
        count_params = {
            k: v for k, v in params.items() if k not in ("per_page", "offset")
        }
        total = self.fetch_scalar(
            f"""
            SELECT COUNT(*)
            FROM glossary_entries
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

    def get_grouping_counts(self) -> dict:
        """Get counts for all filter categories."""

        # Total count
        all_count = self.fetch_scalar("SELECT COUNT(*) FROM glossary_entries") or 0

        # POS counts
        pos_rows = self.fetch_all("""
            SELECT pos, COUNT(*) as count
            FROM glossary_entries
            WHERE pos IS NOT NULL AND pos != ''
            GROUP BY pos
            ORDER BY count DESC
        """)
        pos_counts = {row["pos"]: row["count"] for row in pos_rows}

        # Language counts (family-based)
        lang_rows = self.fetch_all("""
            SELECT
                CASE
                    WHEN language LIKE 'akk%%' THEN 'akk'
                    WHEN language LIKE 'sux%%' THEN 'sux'
                    WHEN language LIKE 'xhu%%' THEN 'xhu'
                    WHEN language LIKE 'elx%%' THEN 'elx'
                    ELSE language
                END as lang_family,
                COUNT(*) as count
            FROM glossary_entries
            WHERE language IS NOT NULL AND language != ''
            GROUP BY lang_family
            ORDER BY count DESC
        """)
        lang_counts = {row["lang_family"]: row["count"] for row in lang_rows}

        # Frequency bucket counts
        freq_counts = {}
        freq_rows = self.fetch_all("""
            SELECT bucket, COUNT(*) as count
            FROM (
                SELECT
                    CASE
                        WHEN icount = 1 THEN '1'
                        WHEN icount BETWEEN 2 AND 10 THEN '2-10'
                        WHEN icount BETWEEN 11 AND 100 THEN '11-100'
                        WHEN icount BETWEEN 101 AND 500 THEN '101-500'
                        WHEN icount > 500 THEN '500+'
                        ELSE 'unknown'
                    END as bucket,
                    CASE
                        WHEN icount = 1 THEN 1
                        WHEN icount BETWEEN 2 AND 10 THEN 2
                        WHEN icount BETWEEN 11 AND 100 THEN 3
                        WHEN icount BETWEEN 101 AND 500 THEN 4
                        WHEN icount > 500 THEN 5
                        ELSE 6
                    END as sort_order
                FROM glossary_entries
                WHERE icount IS NOT NULL
            ) buckets
            GROUP BY bucket, sort_order
            ORDER BY sort_order
        """)
        for row in freq_rows:
            if row["bucket"] != "unknown":
                freq_counts[row["bucket"]] = row["count"]

        return {
            "all": all_count,
            "pos": pos_counts,
            "language": lang_counts,
            "frequency": freq_counts,
        }

    def find_by_entry_id(self, entry_id: str) -> dict | None:
        """Get full entry detail with related data."""

        # Base entry
        entry = self.fetch_one(
            """
            SELECT entry_id, headword, citation_form, guide_word,
                   language, pos, icount, project
            FROM glossary_entries
            WHERE entry_id = %(entry_id)s
        """,
            {"entry_id": entry_id},
        )

        if not entry:
            return None

        # Variants (orthographic forms)
        variants = self.fetch_all(
            """
            SELECT form, count, norm, lang
            FROM glossary_forms
            WHERE entry_id = %(entry_id)s
            ORDER BY count DESC
            LIMIT 20
        """,
            {"entry_id": entry_id},
        )

        # Senses (glosses)
        senses = self.fetch_all(
            """
            SELECT sense_number, guide_word, definition, pos
            FROM glossary_senses
            WHERE entry_id = %(entry_id)s
            ORDER BY sense_number
        """,
            {"entry_id": entry_id},
        )

        # Related words
        related = self.fetch_all(
            """
            SELECT gr.to_entry_id, gr.relationship_type,
                   ge.citation_form, ge.guide_word, ge.language, ge.pos
            FROM glossary_relationships gr
            JOIN glossary_entries ge ON gr.to_entry_id = ge.entry_id
            WHERE gr.from_entry_id = %(entry_id)s
            ORDER BY gr.relationship_type, ge.citation_form
        """,
            {"entry_id": entry_id},
        )

        return {
            "entry": entry,
            "variants": variants,
            "senses": senses,
            "related_words": related,
        }

    def get_attestations(self, entry_id: str, limit: int = 100) -> list[dict]:
        """Get corpus attestations for this entry."""

        # Join to lemmatizations table
        attestations = self.fetch_all(
            """
            SELECT DISTINCT
                a.p_number,
                a.period,
                a.provenience,
                a.genre
            FROM lemmatizations l
            JOIN tokens t ON l.token_id = t.id
            JOIN text_lines tl ON t.line_id = tl.id
            JOIN artifacts a ON tl.p_number = a.p_number
            WHERE l.entry_id = %(entry_id)s
            ORDER BY a.p_number
            LIMIT %(limit)s
        """,
            {"entry_id": entry_id, "limit": limit},
        )

        return attestations
