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
        """Return session joined with user, or None if not found / expired / revoked.

        NOTE: this hand-lists the user columns and so silently drops any new
        users column until someone adds it here (the #450 / #461 class of bug:
        avatar_url/role/theme were all missing once). The auth middleware does
        NOT rely on these user columns — it uses ``resolve_session`` below to get
        the user_id, then reloads the full row via ``UserRepository.find_by_id``
        so future columns are present automatically. This method is retained for
        the repository-level tests and any caller that wants the joined shape.
        """
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
                u.email_verified_at,
                u.avatar_url,
                u.role,
                u.theme
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = %(token_hash)s
              AND s.expires_at > now()
            """,
            {"token_hash": token_hash},
        )

    def resolve_session(self, token_hash: str) -> Optional[dict]:
        """Resolve a session token to its session id + user id only.

        Returns ``{"session_id": ..., "user_id": ...}`` for a live (unexpired)
        session, or ``None``. Deliberately selects NO user columns — the caller
        reloads the full users row via ``UserRepository.find_by_id`` so any
        future users column is automatically reflected on the session auth path
        without editing this query (the #461 fix; mirrors the API-key path).
        """
        return self.fetch_one(
            """
            SELECT
                s.id      AS session_id,
                s.user_id AS user_id
            FROM user_sessions s
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
