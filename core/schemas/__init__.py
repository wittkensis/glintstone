"""Pydantic schemas — the single source of truth for both REST and MCP.

Every API request/response shape and every MCP tool input/output lives here.
The OpenAPI spec at `data-model/glintstone-schema-api.yaml` is generated from
these models; do not hand-edit it.

See `.claude/skills/gs-expert-agentic/SKILL.md` for the contract.
"""

from core.schemas.sources import (
    SourceRef,
    Attribution,
    AnnotationRunRef,
)
from core.schemas.citation import (
    Citation,
    SourceKind,
)
from core.schemas.envelope import (
    ToolResponse,
    FollowUp,
    RenderHint,
    # payloads
    TablePayload,
    GroupedTablePayload,
    Group,
    CardPayload,
    Field,
    Badge,
    BestGuess,
    ChainPayload,
    ChainStep,
    Hypothesis,
    TimelinePayload,
    TimelineEvent,
    MapPayload,
    MapPoint,
    ListPayload,
)
from core.schemas.search import (
    SearchParams,
    SearchMode,
    EntityType,
)
from core.schemas.agent import (
    ArtifactSummaryParams,
    SummaryFocus,
    TokenInterpretParams,
)

__all__ = [
    # sources
    "SourceRef",
    "Attribution",
    "AnnotationRunRef",
    # citations
    "Citation",
    "SourceKind",
    # envelope
    "ToolResponse",
    "FollowUp",
    "RenderHint",
    "TablePayload",
    "GroupedTablePayload",
    "Group",
    "CardPayload",
    "Field",
    "Badge",
    "BestGuess",
    "ChainPayload",
    "ChainStep",
    "Hypothesis",
    "TimelinePayload",
    "TimelineEvent",
    "MapPayload",
    "MapPoint",
    "ListPayload",
    # search
    "SearchParams",
    "SearchMode",
    "EntityType",
    # agent
    "ArtifactSummaryParams",
    "SummaryFocus",
    "TokenInterpretParams",
]
