"""Agent tool parameters — summarize_artifact, interpret_token."""

from typing import Literal

from pydantic import BaseModel, Field as PField

SummaryFocus = Literal["general", "research", "translation_status"]


class ArtifactSummaryParams(BaseModel):
    p_number: str = PField(description="CDLI P-number, e.g. 'P227657'")
    focus: SummaryFocus = "general"


class TokenInterpretParams(BaseModel):
    p_number: str
    token_id: int = PField(description="tokens.id — call walk_token first to discover")


class CorrectionParams(BaseModel):
    """User-submitted correction of an agent claim. Becomes a new annotation_run."""

    interaction_id: int = PField(
        description="The agent_interactions row being corrected"
    )
    claim: str = PField(description="What the agent said")
    correction: str = PField(description="What the scholar says is correct")
    scholar_id: int | None = None
    evidence: str | None = PField(
        default=None, description="Citation supporting the correction"
    )
