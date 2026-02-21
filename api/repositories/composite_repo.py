"""
Repository for composite text data.
Composites are scholarly reconstructions combining multiple fragmentary tablets.
"""

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
        return self.fetch_all("""
            SELECT
                q_number,
                designation,
                language,
                period,
                genre,
                exemplar_count
            FROM composites
            ORDER BY q_number
            LIMIT %(limit)s OFFSET %(offset)s
        """, {"limit": limit, "offset": offset})

    def find_by_q_number(self, q_number: str) -> dict | None:
        """
        Get a single composite by Q-number.

        Args:
            q_number: The composite Q-number (e.g., "Q000001")

        Returns:
            Composite dictionary or None if not found
        """
        return self.fetch_one("""
            SELECT
                q_number,
                designation,
                language,
                period,
                genre,
                exemplar_count
            FROM composites
            WHERE q_number = %(q_number)s
        """, {"q_number": q_number})

    def get_exemplars(self, q_number: str) -> list[dict]:
        """
        Get all exemplar tablets for a composite.

        Args:
            q_number: The composite Q-number

        Returns:
            List of artifact dictionaries that are exemplars of this composite
        """
        return self.fetch_all("""
            SELECT
                a.p_number,
                a.designation,
                a.period,
                a.provenience,
                a.genre,
                ac.line_ref,
                ac.notes
            FROM artifacts a
            JOIN artifact_composites ac ON a.p_number = ac.p_number
            WHERE ac.q_number = %(q_number)s
            ORDER BY a.p_number
        """, {"q_number": q_number})

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
        offset: int = 0
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
        params = {"limit": limit, "offset": offset}

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

        return self.fetch_all(f"""
            SELECT
                q_number,
                designation,
                language,
                period,
                genre,
                exemplar_count
            FROM composites
            {where}
            ORDER BY q_number
            LIMIT %(limit)s OFFSET %(offset)s
        """, params)
