"""Repository for user sessions."""

from datetime import datetime
from typing import Optional, cast

from core.repository import BaseRepository


class SessionRepository(BaseRepository):
    def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        # INSERT ... RETURNING * always yields exactly one row, so the
        # Optional from fetch_one is never None here.
        return cast(
            dict,
            self.fetch_one(
                """
            INSERT INTO user_sessions (user_id, token_hash, expires_at, ip, user_agent)
            VALUES (%(user_id)s, %(token_hash)s, %(expires_at)s, %(ip)s, %(user_agent)s)
            RETURNING *
            """,
                {
                    "user_id": user_id,
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                    "ip": ip,
                    "user_agent": user_agent,
                },
            ),
        )

    def find_by_token_hash(self, token_hash: str) -> Optional[dict]:
        """Return session joined with user, or None if not found / expired / revoked."""
        return self.fetch_one(
            """
            SELECT
                s.id            AS session_id,
                s.expires_at,
                s.last_seen_at,
                u.id            AS id,
                u.email,
                u.display_name,
                u.orcid_id,
                u.email_verified_at
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = %(token_hash)s
              AND s.expires_at > now()
            """,
            {"token_hash": token_hash},
        )

    def touch(self, session_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE user_sessions SET last_seen_at = now() WHERE id = %(id)s",
                {"id": session_id},
            )

    def revoke(self, session_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_sessions WHERE id = %(id)s",
                {"id": session_id},
            )
