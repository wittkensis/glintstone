"""Collection repository — CRUD and member management."""

import math

from core.repository import BaseRepository


class CollectionRepository(BaseRepository):

    def get_all(self) -> list[dict]:
        collections = self.fetch_all("""
            SELECT c.collection_id, c.name, c.description, c.image_path,
                   c.created_at, c.updated_at,
                   COUNT(cm.p_number) AS tablet_count
            FROM collections c
            LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
            GROUP BY c.collection_id
            ORDER BY c.created_at DESC
        """)

        # Attach preview tablets
        for coll in collections:
            coll["preview_tablets"] = self.get_preview_tablets(coll["collection_id"])

        return collections

    def get_random(self, limit: int = 3) -> list[dict]:
        collections = self.fetch_all("""
            SELECT c.collection_id, c.name, c.description, c.image_path,
                   c.created_at, c.updated_at,
                   COUNT(cm.p_number) AS tablet_count
            FROM collections c
            LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
            GROUP BY c.collection_id
            HAVING COUNT(cm.p_number) > 0
            ORDER BY RANDOM()
            LIMIT %(limit)s
        """, {"limit": limit})

        for coll in collections:
            coll["preview_tablets"] = self.get_preview_tablets(coll["collection_id"])

        return collections

    def find_by_id(self, collection_id: int) -> dict | None:
        coll = self.fetch_one("""
            SELECT c.*, COUNT(cm.p_number) AS tablet_count
            FROM collections c
            LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
            WHERE c.collection_id = %(id)s
            GROUP BY c.collection_id
        """, {"id": collection_id})
        return coll

    def get_tablets(self, collection_id: int, page: int = 1, per_page: int = 24) -> dict:
        offset = (page - 1) * per_page

        items = self.fetch_all("""
            SELECT a.p_number, a.designation, a.language, a.period,
                   a.provenience, a.genre,
                   ps.physical_complete, ps.graphemic_complete,
                   ps.reading_complete, ps.linguistic_complete,
                   ps.semantic_complete, ps.has_image
            FROM collection_members cm
            JOIN artifacts a ON cm.p_number = a.p_number
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE cm.collection_id = %(id)s
            ORDER BY a.p_number
            LIMIT %(per_page)s OFFSET %(offset)s
        """, {"id": collection_id, "per_page": per_page, "offset": offset})

        total = self.fetch_scalar("""
            SELECT COUNT(*) FROM collection_members WHERE collection_id = %(id)s
        """, {"id": collection_id})

        total = total or 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page) if per_page else 0,
        }

    def get_preview_tablets(self, collection_id: int, limit: int = 4) -> list[dict]:
        return self.fetch_all("""
            SELECT a.p_number, a.designation
            FROM collection_members cm
            JOIN artifacts a ON cm.p_number = a.p_number
            WHERE cm.collection_id = %(id)s
            LIMIT %(limit)s
        """, {"id": collection_id, "limit": limit})

    def create(self, name: str, description: str | None = None) -> dict:
        return self.fetch_one("""
            INSERT INTO collections (name, description, created_at, updated_at)
            VALUES (%(name)s, %(desc)s, NOW(), NOW())
            RETURNING collection_id, name, description, image_path, created_at, updated_at
        """, {"name": name, "desc": description or ""})

    def update(self, collection_id: int, name: str, description: str | None = None) -> dict:
        return self.fetch_one("""
            UPDATE collections
            SET name = %(name)s, description = %(desc)s, updated_at = NOW()
            WHERE collection_id = %(id)s
            RETURNING collection_id, name, description, image_path, created_at, updated_at
        """, {"id": collection_id, "name": name, "desc": description or ""})

    def delete(self, collection_id: int) -> bool:
        self.fetch_all(
            "DELETE FROM collection_members WHERE collection_id = %(id)s",
            {"id": collection_id},
        )
        self.fetch_all(
            "DELETE FROM collections WHERE collection_id = %(id)s",
            {"id": collection_id},
        )
        self.conn.commit()
        return True

    def add_tablets(self, collection_id: int, p_numbers: list[str]) -> int:
        added = 0
        for pn in p_numbers:
            try:
                self.fetch_all("""
                    INSERT INTO collection_members (collection_id, p_number)
                    VALUES (%(cid)s, %(pn)s)
                    ON CONFLICT DO NOTHING
                """, {"cid": collection_id, "pn": pn})
                added += 1
            except Exception:
                pass

        self.fetch_all(
            "UPDATE collections SET updated_at = NOW() WHERE collection_id = %(id)s",
            {"id": collection_id},
        )
        self.conn.commit()
        return added

    def remove_tablet(self, collection_id: int, p_number: str) -> bool:
        self.fetch_all("""
            DELETE FROM collection_members
            WHERE collection_id = %(cid)s AND p_number = %(pn)s
        """, {"cid": collection_id, "pn": p_number})

        self.fetch_all(
            "UPDATE collections SET updated_at = NOW() WHERE collection_id = %(id)s",
            {"id": collection_id},
        )
        self.conn.commit()
        return True
