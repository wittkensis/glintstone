"""Period repository — canonical historical periods with BCE date ranges.

Reads the `period_canon` lookup table, which maps many raw CDLI period
strings to a smaller set of canonical period names (e.g. "Old Babylonian")
each carrying a scholarly-consensus date range in BCE.

The table's primary key is `raw_period`, so a single canonical period can
appear under several raw spellings. This repository deduplicates to one row
per canonical name (mirroring ArtifactRepository.get_filter_options) so the
timeline gets a clean chronological list of distinct periods.
"""

from core.repository import BaseRepository


class PeriodRepository(BaseRepository):
    def get_canonical_periods(self) -> list[dict]:
        """Return one row per canonical period, ordered chronologically.

        Each row: {canonical, date_start_bce, date_end_bce, sort_order,
        group_name}. BCE dates are stored as negative integers (or null when
        a period has no agreed range, e.g. "Uncertain"). Rows are ordered by
        sort_order (nulls last) so the consumer can lay them out left-to-right
        in chronological order without re-sorting.
        """
        return self.fetch_all(
            """
            SELECT canonical, date_start_bce, date_end_bce,
                   sort_order, group_name
            FROM (
                SELECT DISTINCT ON (canonical)
                    canonical,
                    date_start_bce,
                    date_end_bce,
                    sort_order,
                    COALESCE(group_name, 'Other') AS group_name
                FROM period_canon
                ORDER BY canonical, sort_order NULLS LAST
            ) pc
            ORDER BY sort_order NULLS LAST, canonical
            """
        )
