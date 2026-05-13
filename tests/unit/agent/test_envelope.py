"""Round-trip + shape tests for the ToolResponse envelope."""

from datetime import datetime


from core.schemas.envelope import (
    CardPayload,
    ChainPayload,
    ChainStep,
    Field,
    FollowUp,
    Group,
    GroupedTablePayload,
    Hypothesis,
    ToolResponse,
)
from core.schemas.citation import Citation
from core.schemas.sources import SourceRef


def _src() -> SourceRef:
    return SourceRef.computed(method="hybrid", label="test")


def test_tool_response_grouped_table_roundtrip():
    group = Group(
        group_type="tablets",
        items=[{"entity_id": "P227657", "score": 0.91}],
        total=247,
        cursor="eyJzY29yZSI6Li4ufQ",
        view_all=FollowUp(
            tool="semantic_search",
            args={"q": "gilgamesh", "types": ["tablets"], "limit": 50},
            label="View all 247 tablets",
        ),
    )
    response = ToolResponse[GroupedTablePayload](
        summary="1/6 entity types matched.",
        data=GroupedTablePayload(groups=[group]),
        sources=[_src()],
        interaction_id="42",
        render_hint="table",
    )

    payload = response.model_dump_json()
    restored = ToolResponse[GroupedTablePayload].model_validate_json(payload)

    assert restored.summary == response.summary
    assert restored.data.groups[0].total == 247
    assert restored.data.groups[0].cursor == "eyJzY29yZSI6Li4ufQ"
    assert restored.data.groups[0].view_all is not None
    assert restored.render_hint == "table"
    assert isinstance(restored.generated_at, datetime)


def test_tool_response_card_with_synthesis_and_citations():
    citation = Citation(
        n=3,
        source_kind="annotation_run",
        source_id=4471,
        retrieval_field="period",
        publication_short="Parpola 1987",
    )
    card = CardPayload(
        title="Gilgamesh tablet",
        subtitle="P227657",
        fields=[Field(label="Period", value="Ur III", sources=[_src()])],
        synthesis="An Ur III tablet from Drehem [1][3].",
        synthesis_citations=[citation],
    )
    response = ToolResponse[CardPayload](
        summary="Ur III tablet from Drehem.",
        data=card,
        sources=[_src()],
        interaction_id="100",
        render_hint="card",
    )
    restored = ToolResponse[CardPayload].model_validate_json(response.model_dump_json())
    assert restored.data.synthesis == "An Ur III tablet from Drehem [1][3]."
    assert restored.data.synthesis_citations[0].n == 3
    assert restored.data.synthesis_citations[0].retrieval_field == "period"


def test_tool_response_chain_with_hypotheses():
    chain = ChainPayload(
        steps=[ChainStep(label="Written form", value="dingir-utu", sources=[_src()])],
        hypotheses=[
            Hypothesis(
                reading="the candidate reading 'Šamaš'",
                confidence_band="high",
                evidence_chain=["attested in ≥1000 contexts", "neighbor lemma 'lumaḫ'"],
                citations=[],
            )
        ],
    )
    response = ToolResponse[ChainPayload](
        summary="Unlemmatized; one strong hypothesis.",
        data=chain,
        sources=[_src()],
        interaction_id="101",
        render_hint="chain",
    )
    restored = ToolResponse[ChainPayload].model_validate_json(
        response.model_dump_json()
    )
    assert restored.data.hypotheses[0].confidence_band == "high"
    assert restored.data.hypotheses[0].reading.startswith("the candidate reading")


def test_sources_must_not_be_empty_via_computed_fallback():
    """The contract is sources[] is never empty. SourceRef.computed() is the fallback."""
    ref = SourceRef.computed(method="grounded-synthesis")
    assert ref.kind == "computed"
    assert ref.method == "grounded-synthesis"
    assert ref.label  # has a default label
