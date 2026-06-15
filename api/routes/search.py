"""REST: GET /api/v2/search — semantic_search.

This route is the thin REST projection of the same service the MCP server
uses. The shared logic lives in api/services/agent_service.py.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from api.dependencies import require_user
from api.ratelimit import limiter, user_or_ip_key
from api.services import agent_service
from core.agent.interactions import log_interaction
from core.database import get_db
from core.schemas.envelope import ToolResponse, GroupedTablePayload
from core.schemas.search import EntityType, SearchMode, SearchParams

router = APIRouter(tags=["agentic"])


@router.get(
    "/search",
    response_model=ToolResponse[GroupedTablePayload],
    summary="Hybrid semantic + lexical search across tablets, lemmas, signs, scholars, entities",
)
@limiter.limit("10/minute", key_func=user_or_ip_key)
def semantic_search(
    request: Request,
    # max_length caps a single query at 500 characters — anything longer is
    # either a corrupted client or abuse. See issue #52.
    q: Annotated[str, Query(description="Free-text query", max_length=500)],
    types: Annotated[
        list[EntityType] | None,
        Query(description="Restrict to these entity types; omit for all"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 5,
    cursor: Annotated[
        str | None,
        Query(description="Opaque, returned by previous response; 5-min TTL"),
    ] = None,
    mode: Annotated[
        SearchMode, Query(description="lexical | semantic | hybrid")
    ] = "hybrid",
    user: dict = Depends(require_user),
    conn=Depends(get_db),
) -> ToolResponse[GroupedTablePayload]:
    params = SearchParams(q=q, types=types, limit=limit, cursor=cursor, mode=mode)
    interaction_id_str = str(uuid.uuid4())

    with log_interaction(
        conn,
        surface="api",
        route_path="/search",
        tool_name="semantic_search",
        request=params.model_dump(mode="json"),
    ) as interaction:
        # PRD-006: agent_outputs snippet enrichment is handled inside do_search —
        # it pre-fetches cached artifact summaries for all tablet hits and attaches
        # snippet text to each tablet result item.
        response = agent_service.do_search(
            conn, params, interaction_id=interaction_id_str
        )
        # Collect result_ids for the learning loop
        result_ids: list[str] = []
        for group in response.data.groups:
            for item in group.items:
                if item.get("p_number"):
                    result_ids.append(item["p_number"])
                elif item.get("entity_id"):
                    result_ids.append(f"{group.group_type}:{item['entity_id']}")
        interaction.record_response(
            summary=response.summary,
            result_ids=result_ids,
            sources_count=len(response.sources),
        )

    # Bind the response to the persisted interaction id (string of int)
    if interaction.id is not None:
        response.interaction_id = str(interaction.id)
    return response
