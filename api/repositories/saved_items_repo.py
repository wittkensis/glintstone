"""Repository for user saved items (bookmarks)."""

from typing import Optional, cast

from core.repository import BaseRepository


class SavedItemsRepository(BaseRepository):
    def list_for_user(
        self, user_id: str, item_type: Optional[str] = None
    ) -> list[dict]:
        if item_type:
            return self.fetch_all(
                """
                SELECT id, item_type, item_id, created_at
                FROM user_saved_items
                WHERE user_id = %(user_id)s AND item_type = %(item_type)s
                ORDER BY created_at DESC
                """,
                {"user_id": user_id, "item_type": item_type},
            )
        return self.fetch_all(
            """
            SELECT id, item_type, item_id, created_at
            FROM user_saved_items
            WHERE user_id = %(user_id)s
            ORDER BY created_at DESC
            """,
            {"user_id": user_id},
        )

    def find_for_item(
        self, user_id: str, item_type: str, item_id: str
    ) -> Optional[dict]:
        return self.fetch_one(
            """
            SELECT id, item_type, item_id, created_at
            FROM user_saved_items
            WHERE user_id = %(user_id)s
              AND item_type = %(item_type)s
              AND item_id = %(item_id)s
            """,
            {"user_id": user_id, "item_type": item_type, "item_id": item_id},
        )

    def save(self, user_id: str, item_type: str, item_id: str) -> dict:
        """Insert or return existing; idempotent via ON CONFLICT DO NOTHING."""
        row = self.fetch_one(
            """
            INSERT INTO user_saved_items (user_id, item_type, item_id)
            VALUES (%(user_id)s, %(item_type)s, %(item_id)s)
            ON CONFLICT (user_id, item_type, item_id) DO NOTHING
            RETURNING id, item_type, item_id, created_at
            """,
            {"user_id": user_id, "item_type": item_type, "item_id": item_id},
        )
        if row is None:
            # DO NOTHING suppressed the RETURNING row, so the item already
            # existed — find_for_item is guaranteed to retrieve it.
            row = self.find_for_item(user_id, item_type, item_id)
        return cast(dict, row)

    def delete(self, item_id: str, user_id: str) -> bool:
        """Returns False if not found or not owned by user."""
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_saved_items WHERE id = %(id)s AND user_id = %(user_id)s",
                {"id": item_id, "user_id": user_id},
            )
            return cur.rowcount > 0
