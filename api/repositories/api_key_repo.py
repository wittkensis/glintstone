"""Repository for API keys."""

from typing import Optional, cast

from core.repository import BaseRepository


class ApiKeyRepository(BaseRepository):
    def create(
        self, user_id: str, key_hash: str, label: str, tier: str = "free"
    ) -> dict:
        # INSERT ... RETURNING always yields exactly one row.
        row = self.fetch_one(
            """
            INSERT INTO api_keys (user_id, key_hash, label, tier)
            VALUES (%(user_id)s, %(key_hash)s, %(label)s, %(tier)s)
            RETURNING id, user_id, label, tier, created_at, last_used_at, revoked_at
            """,
            {"user_id": user_id, "key_hash": key_hash, "label": label, "tier": tier},
        )
        return cast(dict, row)

    def find_by_hash(self, key_hash: str) -> Optional[dict]:
        """Return active key row, or None if not found or revoked."""
        return self.fetch_one(
            """
            SELECT k.id, k.user_id, k.label, k.tier, k.last_used_at
            FROM api_keys k
            WHERE k.key_hash = %(key_hash)s
              AND k.revoked_at IS NULL
            """,
            {"key_hash": key_hash},
        )

    def touch(self, key_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE api_keys SET last_used_at = now() WHERE id = %(id)s",
                {"id": key_id},
            )

    def list_for_user(self, user_id: str) -> list[dict]:
        return self.fetch_all(
            """
            SELECT id, label, tier, created_at, last_used_at,
                   revoked_at IS NOT NULL AS is_revoked
            FROM api_keys
            WHERE user_id = %(user_id)s
            ORDER BY created_at DESC
            """,
            {"user_id": user_id},
        )

    def revoke(self, key_id: str, user_id: str) -> bool:
        """Revoke a key; returns False if not found or not owned by user."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE api_keys
                SET revoked_at = now()
                WHERE id = %(id)s AND user_id = %(user_id)s AND revoked_at IS NULL
                """,
                {"id": key_id, "user_id": user_id},
            )
            return cur.rowcount > 0
