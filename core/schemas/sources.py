"""Source references and attributions.

A `SourceRef` is what we attach to every value an agent surfaces, so the caller
knows where it came from. `Attribution` carries the cite-this-source-please
requirement that comes with eBL / ORACC content. `AnnotationRunRef` is the
canonical pointer into `annotation_runs`.
"""

from typing import Literal

from pydantic import BaseModel, Field as PField


class AnnotationRunRef(BaseModel):
    """Pointer into `annotation_runs`. The canonical 'where did this come from'."""

    run_id: int
    source_name: str = PField(
        description="e.g. 'cdli_catalog', 'oracc_etcsri', 'epsd2', 'user-correction'"
    )
    method: str | None = PField(
        default=None,
        description="e.g. 'import', 'lemmatization', 'agent-hypothesis', 'collation'",
    )
    scholar_id: int | None = None
    scholar_name: str | None = None
    publication_short: str | None = None
    created_at: str | None = None


class SourceRef(BaseModel):
    """A source for one value or claim. Never empty on a ToolResponse."""

    kind: Literal[
        "annotation_run",
        "publication",
        "authority_link",
        "computed",
        "lexical_lemma",
        "named_entity",
    ]
    label: str = PField(
        description="Human-readable: 'CDLI catalog (2024)' or 'Šamaš entity (oid 12345)'"
    )
    annotation_run: AnnotationRunRef | None = None
    publication_id: int | None = None
    authority_url: str | None = None
    method: str | None = PField(
        default=None,
        description="For kind='computed' — e.g. 'voyage-3-large/cosine', 'pg_trgm_similarity'",
    )

    @classmethod
    def computed(cls, method: str, label: str | None = None) -> "SourceRef":
        return cls(kind="computed", method=method, label=label or f"computed:{method}")


class Attribution(BaseModel):
    """A required citation surfaced to the caller (e.g. eBL terms-of-use).

    `required_attributions` on `ToolResponse` is non-strippable — clients must
    surface it when the underlying data contributed to the response.
    """

    source: str = PField(description="e.g. 'eBL', 'ORACC/saao', 'CDLI'")
    citation: str = PField(
        description="Short citation text to display alongside results"
    )
    url: str | None = None
    license: str | None = None
