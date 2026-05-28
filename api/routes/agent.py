"""REST: GET /api/v2/artifacts/{p}/summary  (summarize_artifact)
        GET /api/v2/artifacts/{p}/tokens/{tid}/interpret  (interpret_token)
        POST /api/v2/agentic/corrections  (user correction → annotation_run)

Thin projection of api/services/agent_service.py — same service the MCP server
hits. Two-tier rule: web app and MCP both go through the REST API.
"""

from __future__ import annotations

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from typing import Literal

from api.services import agent_service
from core.agent.interactions import log_interaction
from core.database import get_db
from core.schemas.agent import (
    ArtifactSummaryParams,
    CorrectionParams,
    SummaryFocus,
    TokenInterpretParams,
)
from core.schemas.envelope import CardPayload, ChainPayload, ToolResponse

router = APIRouter(prefix="/artifacts", tags=["agentic"])


@router.get(
    "/{p_number}/summary",
    response_model=ToolResponse[CardPayload],
    summary="Grounded summary of an artifact with citations + best-guess for sparse tablets",
)
def summarize_artifact(
    p_number: Annotated[str, Path()],
    focus: SummaryFocus = "general",
    conn=Depends(get_db),
) -> ToolResponse[CardPayload]:
    params = ArtifactSummaryParams(p_number=p_number, focus=focus)
    interaction_id_str = str(uuid.uuid4())

    with log_interaction(
        conn,
        surface="api",
        route_path="/artifacts/{p}/summary",
        tool_name="summarize_artifact",
        request=params.model_dump(mode="json"),
    ) as interaction:
        response = agent_service.do_summarize_artifact(
            conn,
            p_number=p_number,
            focus=focus,
            interaction_id_int=None,
            interaction_id_str=interaction_id_str,
        )
        interaction.record_response(
            summary=response.summary,
            result_ids=[p_number],
            sources_count=len(response.sources),
        )

    if interaction.id is not None:
        response.interaction_id = str(interaction.id)
    return response


@router.get(
    "/{p_number}/tokens/{token_id}/interpret",
    response_model=ToolResponse[ChainPayload],
    summary="Grounded token interpretation — chain when lemmatized, hypotheses when not",
)
def interpret_token(
    p_number: Annotated[str, Path()],
    token_id: Annotated[int, Path()],
    conn=Depends(get_db),
) -> ToolResponse[ChainPayload]:
    params = TokenInterpretParams(p_number=p_number, token_id=token_id)
    interaction_id_str = str(uuid.uuid4())

    with log_interaction(
        conn,
        surface="api",
        route_path="/artifacts/{p}/tokens/{tid}/interpret",
        tool_name="interpret_token",
        request=params.model_dump(mode="json"),
    ) as interaction:
        response = agent_service.do_interpret_token(
            conn,
            p_number=p_number,
            token_id=token_id,
            interaction_id_int=None,
            interaction_id_str=interaction_id_str,
        )
        interaction.record_response(
            summary=response.summary,
            result_ids=[p_number, f"token:{token_id}"],
            sources_count=len(response.sources),
        )

    if interaction.id is not None:
        response.interaction_id = str(interaction.id)
    return response


# ── Feedback + Corrections ────────────────────────────────────────────────────


corrections_router = APIRouter(prefix="/agentic", tags=["agentic"])


class FeedbackParams(BaseModel):
    interaction_id: int
    rating: Literal["up", "down"]


class FeedbackResponse(BaseModel):
    feedback_id: int


@corrections_router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Record a thumbs-up/down rating for any agent interaction",
)
def submit_feedback(
    body: FeedbackParams,
    conn=Depends(get_db),
) -> FeedbackResponse:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM agent_interactions WHERE id = %s",
            (body.interaction_id,),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="interaction_id not found")

        cur.execute(
            """
            INSERT INTO interaction_feedback (interaction_id, kind, payload)
            VALUES (%s, 'explicit_rating', %s::jsonb)
            RETURNING id
            """,
            (body.interaction_id, json.dumps({"rating": body.rating})),
        )
        feedback_id = cur.fetchone()["id"]
    conn.commit()
    return FeedbackResponse(feedback_id=feedback_id)


class CorrectionResponse(BaseModel):
    interaction_id: int
    feedback_id: int
    new_annotation_run_id: int | None = None
    message: str


@corrections_router.post(
    "/corrections",
    response_model=CorrectionResponse,
    summary="Record a scholar correction → interaction_feedback + new annotation_run",
)
def submit_correction(
    body: CorrectionParams,
    conn=Depends(get_db),
) -> CorrectionResponse:
    """Corrections flow into the existing trust infrastructure as a new
    annotation_runs row with method='agent-hypothesis-correction'. The
    affected agent_outputs row will be marked superseded on the next
    summarize_artifact call automatically (via _has_newer_annotation_run)."""
    with conn.cursor() as cur:
        # 1. Verify the interaction exists
        cur.execute(
            "SELECT id FROM agent_interactions WHERE id = %s",
            (body.interaction_id,),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="interaction_id not found")

        # 2. New annotation_run for the correction
        cur.execute(
            """
            INSERT INTO annotation_runs (source_name, method, scholar_id)
            VALUES ('user-correction', 'agent-hypothesis-correction', %s)
            RETURNING id
            """,
            (body.scholar_id,),
        )
        new_run_id = cur.fetchone()["id"]

        # 3. interaction_feedback row
        cur.execute(
            """
            INSERT INTO interaction_feedback (
                interaction_id, kind, payload, scholar_id
            )
            VALUES (%s, 'correction', %s::jsonb, %s)
            RETURNING id
            """,
            (
                body.interaction_id,
                json.dumps(
                    {
                        "claim": body.claim,
                        "correction": body.correction,
                        "evidence": body.evidence,
                        "new_annotation_run_id": new_run_id,
                    }
                ),
                body.scholar_id,
            ),
        )
        feedback_id = cur.fetchone()["id"]
    conn.commit()

    return CorrectionResponse(
        interaction_id=body.interaction_id,
        feedback_id=feedback_id,
        new_annotation_run_id=new_run_id,
        message=(
            "Correction recorded. The next request that re-loads any agent "
            "output citing the corrected annotation will regenerate."
        ),
    )
