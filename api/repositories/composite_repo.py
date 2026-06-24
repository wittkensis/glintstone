"""
Repository for composite text data.
Composites are scholarly reconstructions combining multiple fragmentary tablets.
"""

from typing import Any

from core.repository import BaseRepository


class CompositeRepository(BaseRepository):
    """Repository for querying composite text data."""

    def find_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Get all composites with pagination.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of composite dictionaries with metadata
        """
        return self.fetch_all(
            """
            SELECT
                q_number,
                designation,
                language,
                period,
                genre,
                exemplar_count
            FROM composites
            ORDER BY exemplar_count DESC, q_number
            LIMIT %(limit)s OFFSET %(offset)s
        """,
            {"limit": limit, "offset": offset},
        )

    def find_by_q_number(self, q_number: str) -> dict | None:
        """
        Get a single composite by Q-number.

        Args:
            q_number: The composite Q-number (e.g., "Q000001")

        Returns:
            Composite dictionary or None if not found
        """
        return self.fetch_one(
            """
            SELECT
                q_number,
                designation,
                language,
                period,
                genre,
                exemplar_count
            FROM composites
            WHERE q_number = %(q_number)s
        """,
            {"q_number": q_number},
        )

    def get_exemplars(self, q_number: str) -> list[dict]:
        """
        Get all exemplar tablets for a composite.

        Args:
            q_number: The composite Q-number

        Returns:
            List of artifact dictionaries that are exemplars of this composite.
            Each row carries ``atf_line_count`` — the number of *readable* ATF
            lines (same non-structural filter as the representative-preview
            query: excludes ``$``/``@``/``&``/``#`` lines). This powers the
            "Extent" column (#404 Concept A): how complete each witness is, from
            data we hold rather than a self-reported field. Witnesses with no
            readable ATF report ``0``.
        """
        return self.fetch_all(
            r"""
            SELECT
                a.p_number,
                a.designation,
                a.period,
                a.provenience,
                a.genre,
                ac.line_ref,
                ps.semantic_complete,
                ps.has_translation,
                COALESCE((
                    SELECT count(*)
                    FROM text_lines tl
                    WHERE tl.p_number = a.p_number
                      AND tl.raw_atf IS NOT NULL
                      AND tl.raw_atf <> ''
                      AND tl.raw_atf !~ '^[$@&#]'
                ), 0) AS atf_line_count
            FROM artifacts a
            JOIN artifact_composites ac ON a.p_number = ac.p_number
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE ac.q_number = %(q_number)s
            ORDER BY a.p_number
        """,
            {"q_number": q_number},
        )

    def get_witness_atf_preview(
        self, q_number: str, p_number: str, limit: int = 8
    ) -> dict | None:
        """First-N readable ATF lines of *one specific* witness (#404 Concept A).

        Generalises ``get_representative_atf_preview`` to any exemplar so the
        witness-switcher can read any witness's text in place, not just the one
        representative. Verifies ``p_number`` is actually linked to ``q_number``
        first (no cross-composite leakage). Same readable-line filter; ``raw_atf``
        returned verbatim. Returns ``None`` when the witness is not linked or has
        no readable ATF, so the caller keeps the current preview unchanged.
        """
        rep = self.fetch_one(
            r"""
            SELECT a.p_number,
                   a.designation,
                   a.period,
                   a.provenience,
                   count(tl.id) AS atf_line_count
            FROM artifact_composites ac
            JOIN artifacts a ON a.p_number = ac.p_number
            JOIN text_lines tl ON tl.p_number = ac.p_number
            WHERE ac.q_number = %(q_number)s
              AND ac.p_number = %(p_number)s
              AND tl.raw_atf IS NOT NULL
              AND tl.raw_atf <> ''
              AND tl.raw_atf !~ '^[$@&#]'
            GROUP BY a.p_number, a.designation, a.period, a.provenience
            """,
            {"q_number": q_number, "p_number": p_number},
        )
        if not rep:
            return None

        lines = self.fetch_all(
            r"""
            SELECT tl.line_number, tl.raw_atf
            FROM text_lines tl
            WHERE tl.p_number = %(p_number)s
              AND tl.raw_atf IS NOT NULL
              AND tl.raw_atf <> ''
              AND tl.raw_atf !~ '^[$@&#]'
            ORDER BY tl.column_number, tl.id
            LIMIT %(limit)s
            """,
            {"p_number": rep["p_number"], "limit": limit},
        )

        return {
            "p_number": rep["p_number"],
            "designation": rep["designation"],
            "period": rep["period"],
            "provenience": rep["provenience"],
            "total_atf_lines": rep["atf_line_count"],
            "preview_line_count": len(lines),
            "lines": lines,
        }

    def get_representative_atf_preview(
        self, q_number: str, limit: int = 8
    ) -> dict | None:
        """Preview of a representative exemplar's transliterated text (#159).

        The composition detail page shows the actual cuneiform transliteration
        (ATF) of one well-preserved exemplar so a reader can see real text, not
        just a list of P-numbers. We pick the *representative* exemplar as the
        linked tablet carrying the most non-empty, non-structural ATF lines —
        i.e. the most complete witness we hold — then return that tablet's first
        ``limit`` readable lines in document order.

        "Readable" excludes ATF structural/metadata lines (those beginning with
        ``$`` strict/loose state notes, ``@`` surface markers, ``&`` headers,
        ``#`` comments) so the preview opens on actual transliterated signs
        rather than a "beginning broken" annotation. The ``raw_atf`` text itself
        is returned verbatim — prime notation, damage brackets ``[...]``, and
        half-bracket damage ``#`` on signs are all preserved exactly as stored.

        Returns ``None`` when no linked exemplar has any readable ATF line, so
        the caller renders the #189 empty state. Never reads
        ``pipeline_completeness`` (it is unreliable — #257).
        """
        # Step 1: choose the representative exemplar — most readable ATF lines.
        rep = self.fetch_one(
            r"""
            SELECT ac.p_number,
                   a.designation,
                   a.period,
                   a.provenience,
                   count(*) AS atf_line_count
            FROM artifact_composites ac
            JOIN text_lines tl ON tl.p_number = ac.p_number
            JOIN artifacts a ON a.p_number = ac.p_number
            WHERE ac.q_number = %(q_number)s
              AND tl.raw_atf IS NOT NULL
              AND tl.raw_atf <> ''
              AND tl.raw_atf !~ '^[$@&#]'
            GROUP BY ac.p_number, a.designation, a.period, a.provenience
            ORDER BY atf_line_count DESC, ac.p_number
            LIMIT 1
            """,
            {"q_number": q_number},
        )
        if not rep:
            return None

        # Step 2: that exemplar's first N readable lines, in document order.
        lines = self.fetch_all(
            r"""
            SELECT tl.line_number, tl.raw_atf
            FROM text_lines tl
            WHERE tl.p_number = %(p_number)s
              AND tl.raw_atf IS NOT NULL
              AND tl.raw_atf <> ''
              AND tl.raw_atf !~ '^[$@&#]'
            ORDER BY tl.column_number, tl.id
            LIMIT %(limit)s
            """,
            {"p_number": rep["p_number"], "limit": limit},
        )

        return {
            "p_number": rep["p_number"],
            "designation": rep["designation"],
            "period": rep["period"],
            "provenience": rep["provenience"],
            "total_atf_lines": rep["atf_line_count"],
            "preview_line_count": len(lines),
            "lines": lines,
        }

    def get_related_composites(self, q_number: str, limit: int = 8) -> list[dict]:
        """Compositions related to ``q_number`` by shared witnesses (#160).

        DATA-GATE (live, 2026-06): the explicit-relation table
        ``intertextuality_links`` is empty (0 rows), and ``composites.genre`` /
        ``composites.period`` / ``composites.designation`` are 0% populated — so
        genre/period adjacency and an explicit relations table are *not* usable
        signals. The one real signal is the **shared exemplar**: two compositions
        that draw on the same physical tablet (a witness linked to both via
        ``artifact_composites``). 170 of 650 compositions have at least one such
        sibling. This is a grounded, structural relation — not a guess.

        For each related composition we return:
          * ``shared_witnesses`` — how many tablets it shares with ``q_number``
            (the relation strength; orders the list)
          * ``shared_p`` — up to 3 sample shared P-numbers (so the scholar can
            verify the link)
          * ``exemplar_count`` — its ORACC-recorded exemplar total
          * ``top_genre`` / ``top_period`` — the most common genre/period across
            its *exemplar tablets* (derived, since the composite row itself
            carries no genre/period). These give the otherwise-label-less
            composition a human-readable descriptor.

        Returns ``[]`` when the composition shares no witness with any other —
        the caller then omits the widget. Never reads ``pipeline_completeness``.
        """
        return self.fetch_all(
            """
            WITH related AS (
                SELECT ac2.q_number AS rel_q,
                       count(DISTINCT ac1.p_number) AS shared_witnesses,
                       (array_agg(DISTINCT ac1.p_number ORDER BY ac1.p_number))[1:3]
                           AS shared_p
                FROM artifact_composites ac1
                JOIN artifact_composites ac2
                    ON ac1.p_number = ac2.p_number
                   AND ac1.q_number <> ac2.q_number
                WHERE ac1.q_number = %(q_number)s
                GROUP BY ac2.q_number
            )
            SELECT
                r.rel_q AS q_number,
                r.shared_witnesses,
                r.shared_p,
                c.designation,
                c.exemplar_count,
                (
                    SELECT a.genre
                    FROM artifact_composites x
                    JOIN artifacts a ON a.p_number = x.p_number
                    WHERE x.q_number = r.rel_q AND a.genre IS NOT NULL AND a.genre <> ''
                    GROUP BY a.genre
                    ORDER BY count(*) DESC
                    LIMIT 1
                ) AS top_genre,
                (
                    SELECT a.period
                    FROM artifact_composites x
                    JOIN artifacts a ON a.p_number = x.p_number
                    WHERE x.q_number = r.rel_q AND a.period IS NOT NULL AND a.period <> ''
                    GROUP BY a.period
                    ORDER BY count(*) DESC
                    LIMIT 1
                ) AS top_period
            FROM related r
            JOIN composites c ON c.q_number = r.rel_q
            ORDER BY r.shared_witnesses DESC, c.exemplar_count DESC, r.rel_q
            LIMIT %(limit)s
            """,
            {"q_number": q_number, "limit": limit},
        )

    def get_total_count(self) -> int:
        """
        Get total number of composites.

        Returns:
            Total count of composites in database
        """
        result = self.fetch_one("SELECT COUNT(*) as count FROM composites")
        return result["count"] if result else 0

    def search(
        self,
        language: str | None = None,
        period: str | None = None,
        genre: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Search composites with filters.

        Args:
            language: Filter by language
            period: Filter by period
            genre: Filter by genre
            search: Full-text search in designation
            limit: Maximum results
            offset: Results to skip

        Returns:
            List of matching composites
        """
        conditions = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if language:
            conditions.append("language = %(language)s")
            params["language"] = language

        if period:
            conditions.append("period = %(period)s")
            params["period"] = period

        if genre:
            conditions.append("genre = %(genre)s")
            params["genre"] = genre

        if search:
            conditions.append("designation ILIKE %(search)s")
            params["search"] = f"%{search}%"

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        return self.fetch_all(
            f"""
            SELECT
                q_number,
                designation,
                language,
                period,
                genre,
                exemplar_count
            FROM composites
            {where}
            ORDER BY exemplar_count DESC, q_number
            LIMIT %(limit)s OFFSET %(offset)s
        """,
            params,
        )
