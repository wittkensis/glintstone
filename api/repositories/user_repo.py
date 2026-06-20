"""Repository for users and their auth method links."""

from typing import Optional, cast

from core.repository import BaseRepository


class UserRepository(BaseRepository):
    def find_by_email(self, email: str) -> Optional[dict]:
        return self.fetch_one(
            "SELECT * FROM users WHERE email = %(email)s",
            {"email": email},
        )

    def find_by_id(self, user_id: str) -> Optional[dict]:
        return self.fetch_one(
            "SELECT * FROM users WHERE id = %(id)s",
            {"id": user_id},
        )

    def find_by_provider(self, provider: str, provider_id: str) -> Optional[dict]:
        return self.fetch_one(
            """
            SELECT u.*
            FROM users u
            JOIN user_auth_methods m ON m.user_id = u.id
            WHERE m.provider = %(provider)s AND m.provider_id = %(provider_id)s
            """,
            {"provider": provider, "provider_id": provider_id},
        )

    def create_user(
        self,
        email: str,
        display_name: Optional[str] = None,
        orcid_id: Optional[str] = None,
    ) -> dict:
        # INSERT ... ON CONFLICT DO UPDATE ... RETURNING always yields a row.
        row = self.fetch_one(
            """
            INSERT INTO users (email, display_name, orcid_id)
            VALUES (%(email)s, %(display_name)s, %(orcid_id)s)
            ON CONFLICT (email) DO UPDATE
                SET display_name = COALESCE(EXCLUDED.display_name, users.display_name),
                    orcid_id     = COALESCE(EXCLUDED.orcid_id,     users.orcid_id)
            RETURNING *
            """,
            {"email": email, "display_name": display_name, "orcid_id": orcid_id},
        )
        return cast(dict, row)

    def link_auth_method(self, user_id: str, provider: str, provider_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_auth_methods (user_id, provider, provider_id)
                VALUES (%(user_id)s, %(provider)s, %(provider_id)s)
                ON CONFLICT (provider, provider_id) DO NOTHING
                """,
                {"user_id": user_id, "provider": provider, "provider_id": provider_id},
            )

    def verify_email(self, user_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET email_verified_at = now() WHERE id = %(id)s",
                {"id": user_id},
            )

    def update_avatar_url(self, user_id: str, avatar_url: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET avatar_url = %(url)s WHERE id = %(id)s",
                {"url": avatar_url, "id": user_id},
            )

    def update_theme(self, user_id: str, theme: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET theme = %(theme)s WHERE id = %(id)s",
                {"theme": theme, "id": user_id},
            )
