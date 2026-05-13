"""Citation contract.

See `.claude/skills/gs-expert-agentic/citation-contract.md` for the full
contract — what the LLM must do, how validation works, and how this will
extend to academic citation styles (Chicago, AAA, BibTeX, CSL-JSON).

The `Citation` object stores decomposed components so future format-pluggable
rendering is a pure projection. Do not pre-render citations to strings here.
"""

from typing import Literal

from pydantic import BaseModel, Field as PField

SourceKind = Literal[
    "annotation_run",
    "publication",
    "authority_link",
    "computed",
    "lexical_lemma",
    "named_entity",
]


class Citation(BaseModel):
    """Bound to a `[n]` marker in synthesis text."""

    n: int = PField(description="The marker number used in synthesis text: '[3]'")
    source_kind: SourceKind
    source_id: int | str
    annotation_run_id: int | None = None

    scholar_id: int | None = None
    scholar_name: str | None = None
    year: int | None = None
    publication_short: str | None = PField(
        default=None,
        description="'Parpola 1987' — the form most casual rendering uses",
    )
    publication_ref: str | None = PField(default=None, description="Full title")
    page_ref: str | None = None
    url: str | None = None

    retrieval_field: str = PField(
        description=(
            "What this citation supports — 'period' | 'lemma:8841' | "
            "'similar_tablet:P227657'. Audit channel for spotting hallucination."
        )
    )
