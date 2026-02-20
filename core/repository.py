"""Base repository with query helpers for PostgreSQL.

Ported from v0.1 PHP BaseRepository — same patterns, Python idioms.
"""

from typing import Any

import psycopg


class BaseRepository:
    """Provides common query utilities. Subclass for each domain."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    def fetch_all(self, sql: str, params: dict | tuple = ()) -> list[dict]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def fetch_one(self, sql: str, params: dict | tuple = ()) -> dict | None:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def fetch_scalar(self, sql: str, params: dict | tuple = ()) -> Any:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            if row is None:
                return None
            # dict_row returns dict; get first value
            return next(iter(row.values()))

    @staticmethod
    def build_in_clause(values: list, prefix: str = "p") -> tuple[str, dict]:
        """Build IN clause with named parameters.

        Returns (clause, params) e.g. ("IN (%(p0)s, %(p1)s)", {"p0": "a", "p1": "b"})
        """
        if not values:
            return "IN (NULL)", {}

        params = {f"{prefix}{i}": v for i, v in enumerate(values)}
        placeholders = ", ".join(f"%({k})s" for k in params)
        return f"IN ({placeholders})", params

    @staticmethod
    def build_like_clause(
        column: str, values: list[str], prefix: str = "like"
    ) -> tuple[str, dict]:
        """Build ILIKE clause for multiple values with OR.

        Uses ILIKE for case-insensitive matching (PostgreSQL).
        """
        if not values:
            return "1=0", {}

        params = {}
        conditions = []
        for i, v in enumerate(values):
            key = f"{prefix}{i}"
            conditions.append(f"{column} ILIKE %({key})s")
            params[key] = f"%{v}%"

        return f"({' OR '.join(conditions)})", params
