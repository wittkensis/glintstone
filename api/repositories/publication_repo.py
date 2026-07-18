"""Publication repository — the query layer that sources a scholar's works.

Publications are the bibliographic record of what a scholar has *written* (as
opposed to the ``artifact_contributors`` ledger, which records what tablets they
*annotated*). A publication is one book / article / edition / dissertation etc.;
the ``publication_authors`` junction links each publication to the scholars who
authored, edited, translated, or contributed to it, carrying their ``role`` and
byline ``position`` on that specific work.

This repository is the single home for the SQL that sources a scholar's
publications. The ``GET /scholars/{id}/publications`` route delegates here so the
route stays thin and the query logic is unit-testable in isolation (against a
mocked connection) without standing up FastAPI.

Data provenance (why an empty result is honest, not a bug): the ``publications``
and ``publication_authors`` rows are ingested from the ORACC bibliographies and
their per-project author credits, then enriched with citation counts. A scholar
with no rows here genuinely has no bibliographic works on record yet — it is not
a silent join failure. The forthcoming ORCID connector (#608) will *add* works
sourced from a researcher's ORCID profile; it does not change the read shape
below, so this repository already returns everything that connector will feed.
"""

from core.repository import BaseRepository

# The 15-value ``publications.publication_type`` enum, mirrored from the CHECK
# constraint on the table (migration 000 baseline). Kept here so the route can
# whitelist an incoming ``?type=`` filter against the *source of truth* for what
# a valid type is, rather than trusting caller input into SQL.
PUBLICATION_TYPES: frozenset[str] = frozenset(
    {
        "monograph",
        "edited_volume",
        "journal_article",
        "series_volume",
        "digital_edition",
        "museum_catalog",
        "dissertation",
        "conference_paper",
        "hand_copy_publication",
        "chapter",
        "proceedings",
        "thesis",
        "report",
        "unpublished",
        "other",
    }
)


class PublicationRepository(BaseRepository):
    """Sources a scholar's publications via the ``publication_authors`` junction."""

    def scholar_exists(self, scholar_id: int) -> bool:
        """True if a ``scholars`` row exists, so a bad id becomes a 404 upstream
        rather than a silent empty list (which would misrepresent the scholar as
        having published nothing)."""
        return (
            self.fetch_one("SELECT 1 FROM scholars WHERE id = %s", (scholar_id,))
            is not None
        )

    def works_summary(self, scholar_id: int) -> dict:
        """Five whole-corpus aggregates for the detail page's stat strip, plus a
        distinct tablets-edited count.

        The strip always describes the scholar's *entire* body of work — it is
        not narrowed by an active ``?type=`` filter — so the reader keeps the
        real totals while filtering the row list below. Returns:
        ``works``, ``total_cites``, ``top_cites``, ``first_year``, ``last_year``,
        ``type_count``, ``tablets_edited``.
        """
        s = self.fetch_one(
            """
            SELECT count(*)                              AS works,
                   coalesce(sum(p.cited_by_count), 0)    AS total_cites,
                   max(p.cited_by_count)                 AS top_cites,
                   min(p.year)                           AS first_year,
                   max(p.year)                           AS last_year,
                   count(DISTINCT p.publication_type)    AS type_count
            FROM publication_authors pa
            JOIN publications p ON p.id = pa.publication_id
            WHERE pa.scholar_id = %s
            """,
            (scholar_id,),
        )
        # `s` is never None here (aggregate over zero rows still yields one row),
        # but guard for the mocked-DB / defensive case.
        s = s or {}
        summary = {
            "works": int(s.get("works") or 0),
            "total_cites": int(s.get("total_cites") or 0),
            "top_cites": s.get("top_cites"),
            "first_year": s.get("first_year"),
            "last_year": s.get("last_year"),
            "type_count": int(s.get("type_count") or 0),
        }

        # Distinct artifacts edited *via* this scholar's publications — the
        # bridge from the bibliographic record back to the tablet corpus.
        tablets = self.fetch_one(
            """
            SELECT count(DISTINCT ae.p_number) AS tablets_edited
            FROM artifact_editions ae
            JOIN publication_authors pa ON pa.publication_id = ae.publication_id
            WHERE pa.scholar_id = %s
            """,
            (scholar_id,),
        )
        summary["tablets_edited"] = int((tablets or {}).get("tablets_edited") or 0)
        return summary

    def type_breakdown(self, scholar_id: int) -> list[dict]:
        """Real per-type counts for the filter pills, busiest first. Whole-corpus
        (ignores any active filter) so the pills always show their true counts.
        Each row: ``{type, count}``."""
        rows = self.fetch_all(
            """
            SELECT p.publication_type AS type, count(*) AS n
            FROM publication_authors pa
            JOIN publications p ON p.id = pa.publication_id
            WHERE pa.scholar_id = %s
            GROUP BY p.publication_type
            ORDER BY n DESC
            """,
            (scholar_id,),
        )
        return [{"type": r["type"], "count": int(r["n"])} for r in rows]

    def list_works(
        self,
        scholar_id: int,
        *,
        limit: int,
        offset: int,
        type_filter: str = "",
    ) -> list[dict]:
        """A page of the scholar's publications, most-cited first then newest.

        ``type_filter`` MUST already be validated against ``PUBLICATION_TYPES``
        by the caller — it is interpolated as a fixed clause, never as a value,
        and the value itself is still bound as a parameter. Sort policy: impact
        before chronology (``cited_by_count DESC NULLS LAST, year DESC NULLS
        LAST``) — the Tufte data-ledger the detail page renders. Each row carries
        the scholar's ``role`` and byline ``position`` on that work.
        """
        type_clause = "AND p.publication_type = %s" if type_filter else ""
        params: list = [scholar_id]
        if type_filter:
            params.append(type_filter)
        params.extend([limit, offset])

        rows = self.fetch_all(
            f"""
            SELECT p.id, p.title, p.short_title, p.publication_type, p.year,
                   p.publisher, p.doi, p.url, p.cited_by_count,
                   pa.role, pa.position
            FROM publication_authors pa
            JOIN publications p ON p.id = pa.publication_id
            WHERE pa.scholar_id = %s
              {type_clause}
            ORDER BY p.cited_by_count DESC NULLS LAST, p.year DESC NULLS LAST
            LIMIT %s OFFSET %s
            """,
            tuple(params),
        )
        return [dict(r) for r in rows]
