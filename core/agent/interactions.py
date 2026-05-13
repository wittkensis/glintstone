"""agent_interactions logging helper.

Every REST route, MCP tool, web call, and debug call records one row here.
The row contains the request, a thin response summary, surfaced result IDs,
and latency. Full response data is NOT stored — keeps the table small and
prevents accidental PII leak.

Use:
    with log_interaction(conn, surface="api", route_path="/search", request={...}) as interaction:
        # ... do work ...
        interaction.record_response(summary="...", result_ids=[...])
    # interaction.id is now populated and committed
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from contextlib import contextmanager
from typing import Iterator

import psycopg

logger = logging.getLogger(__name__)


@dataclass
class Interaction:
    surface: str
    request: dict
    session_id: str
    tool_name: str | None = None
    route_path: str | None = None
    client_label: str | None = None
    started_at: float = field(default_factory=time.monotonic)
    id: int | None = None

    # Response fields filled by record_response()
    _summary: str | None = None
    _result_ids: list[str] = field(default_factory=list)
    _sources_count: int = 0
    _error_code: str | None = None

    def record_response(
        self,
        summary: str,
        result_ids: list[str] | None = None,
        sources_count: int = 0,
    ) -> None:
        self._summary = summary
        self._result_ids = result_ids or []
        self._sources_count = sources_count

    def record_error(self, error_code: str) -> None:
        self._error_code = error_code

    @property
    def latency_ms(self) -> int:
        return int((time.monotonic() - self.started_at) * 1000)


def _default_session_id() -> str:
    """Per-process session UUID. For MCP stdio this is the agent's
    conversation lifetime; for HTTP it's per-request (HTTP middleware
    overrides this)."""
    return str(uuid.uuid4())


def _client_label_from_env() -> str | None:
    return os.environ.get("GS_CLIENT_LABEL")


@contextmanager
def log_interaction(
    conn: psycopg.Connection,
    *,
    surface: str,
    request: dict,
    session_id: str | None = None,
    tool_name: str | None = None,
    route_path: str | None = None,
    client_label: str | None = None,
) -> Iterator[Interaction]:
    """Context manager that opens an agent_interactions row on enter and
    finalizes it on exit. The row is INSERTed only on exit so latency_ms is
    accurate.

    Yields the Interaction so the caller can attach response details and
    later read .id (set after exit).
    """
    interaction = Interaction(
        surface=surface,
        request=request,
        session_id=session_id or _default_session_id(),
        tool_name=tool_name,
        route_path=route_path,
        client_label=client_label or _client_label_from_env(),
    )

    try:
        yield interaction
    except BaseException as exc:
        interaction.record_error(type(exc).__name__)
        raise
    finally:
        # Always record, even on exception — gives us the request that failed
        try:
            response_summary = (
                {
                    "summary": interaction._summary,
                    "sources_count": interaction._sources_count,
                }
                if interaction._summary
                else None
            )

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_interactions (
                        session_id, surface, tool_name, route_path,
                        request, response_summary, result_ids,
                        latency_ms, error_code, client_label
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        interaction.session_id,
                        interaction.surface,
                        interaction.tool_name,
                        interaction.route_path,
                        json.dumps(interaction.request, default=str),
                        json.dumps(response_summary) if response_summary else None,
                        interaction._result_ids,
                        interaction.latency_ms,
                        interaction._error_code,
                        interaction.client_label,
                    ),
                )
                interaction.id = cur.fetchone()["id"]
            conn.commit()
        except Exception as log_exc:
            # Logging must not break the actual response. Just warn.
            logger.warning("agent_interactions insert failed: %s", log_exc)
            try:
                conn.rollback()
            except Exception:
                pass
