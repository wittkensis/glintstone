"""Stats repository — KPI and aggregate metrics."""

from core.repository import BaseRepository


class StatsRepository(BaseRepository):
    def get_kpi(self) -> dict:
        total = self.fetch_scalar("SELECT COUNT(*) FROM artifacts")

        layer_counts = self.fetch_one("""
            SELECT
                COUNT(*) FILTER (WHERE physical_complete > 0) AS physical_count,
                COUNT(*) FILTER (WHERE graphemic_complete > 0) AS graphemic_count,
                COUNT(*) FILTER (WHERE reading_complete > 0) AS reading_count,
                COUNT(*) FILTER (WHERE linguistic_complete > 0) AS linguistic_count,
                COUNT(*) FILTER (WHERE semantic_complete > 0) AS semantic_count
            FROM pipeline_status
        """)

        top_languages = self.fetch_all("""
            SELECT language, COUNT(*) AS count
            FROM artifacts
            WHERE language IS NOT NULL AND language != ''
            GROUP BY language
            ORDER BY count DESC
            LIMIT 5
        """)

        top_periods = self.fetch_all("""
            SELECT period, COUNT(*) AS count
            FROM artifacts
            WHERE period IS NOT NULL AND period != ''
            GROUP BY period
            ORDER BY count DESC
            LIMIT 5
        """)

        top_genres = self.fetch_all("""
            SELECT genre, COUNT(*) AS count
            FROM artifacts
            WHERE genre IS NOT NULL AND genre != ''
            GROUP BY genre
            ORDER BY count DESC
            LIMIT 5
        """)

        lc = layer_counts or {}
        return {
            "total_tablets": total or 0,
            "pipeline_stages": {
                "physical": {
                    "count": lc.get("physical_count", 0),
                    "percent": round((lc.get("physical_count", 0) / total * 100), 1)
                    if total
                    else 0,
                },
                "graphemic": {
                    "count": lc.get("graphemic_count", 0),
                    "percent": round((lc.get("graphemic_count", 0) / total * 100), 1)
                    if total
                    else 0,
                },
                "reading": {
                    "count": lc.get("reading_count", 0),
                    "percent": round((lc.get("reading_count", 0) / total * 100), 1)
                    if total
                    else 0,
                },
                "linguistic": {
                    "count": lc.get("linguistic_count", 0),
                    "percent": round((lc.get("linguistic_count", 0) / total * 100), 1)
                    if total
                    else 0,
                },
                "semantic": {
                    "count": lc.get("semantic_count", 0),
                    "percent": round((lc.get("semantic_count", 0) / total * 100), 1)
                    if total
                    else 0,
                },
            },
            "top_languages": top_languages,
            "top_periods": top_periods,
            "top_genres": top_genres,
        }
