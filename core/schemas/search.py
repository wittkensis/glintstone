"""Search parameters — shared between REST /search and MCP semantic_search."""

from typing import Literal

from pydantic import BaseModel, Field as PField

SearchMode = Literal["lexical", "semantic", "hybrid"]

EntityType = Literal[
    "tablets",
    "composites",
    "lemmas",
    "signs",
    "glosses",
    "scholars",
    "publications",
    "entities",
    "collections",
]


class SearchFilters(BaseModel):
    """Optional structured filters applied on top of free-text query."""

    period: list[str] | None = None
    provenience: list[str] | None = None
    language: list[str] | None = None
    genre: list[str] | None = None
    pos: list[str] | None = PField(
        default=None, description="Part-of-speech for lemma searches"
    )
    min_completeness: int | None = PField(
        default=None, ge=0, le=5, description="Pipeline completeness floor (0-5)"
    )


class SearchParams(BaseModel):
    q: str = PField(description="Free-text query — keywords, P-number, phrase, etc.")
    types: list[EntityType] | None = PField(
        default=None, description="Restrict to these entity types; null = all"
    )
    limit: int = PField(default=5, ge=1, le=100, description="Per-group limit")
    cursor: str | None = PField(
        default=None, description="Opaque, returned by previous response; 5-min TTL"
    )
    mode: SearchMode = "hybrid"
    filters: SearchFilters | None = None
