"""Test the synthesis loop with a mocked Anthropic client.

Verifies:
- Happy path: validator passes first try → no retry
- Retry path: validator fails, second call passes → retried=True
- Hard fail: two failures → SynthesisGroundingError raised
"""

import pytest

from core.agent.anthropic_client import CompletionResult
from core.agent.citation_parser import SynthesisGroundingError
from core.agent.fact_assembly import ArtifactFactBundle, Fact
from core.agent.synthesis import synthesize_artifact_summary
from core.schemas.citation import Citation


class _MockAnthropic:
    """Records calls and returns scripted responses."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls = 0
        self.model = "claude-sonnet-4-6"

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2048,
        effort: str = "medium",
    ):
        text = self._responses[self.calls] if self.calls < len(self._responses) else ""
        self.calls += 1
        return CompletionResult(
            text=text,
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=80,
            cache_creation_tokens=0,
            model=self.model,
            stop_reason="end_turn",
        )


def _bundle(best_guess: bool = False) -> ArtifactFactBundle:
    bundle = ArtifactFactBundle(p_number="P000001")
    bundle.facts = [
        Fact(
            n=1,
            text="period: Ur III",
            citation=Citation(
                n=1, source_kind="annotation_run", source_id=1, retrieval_field="period"
            ),
        ),
        Fact(
            n=2,
            text="provenience: Drehem",
            citation=Citation(
                n=2,
                source_kind="annotation_run",
                source_id=1,
                retrieval_field="provenience",
            ),
        ),
        Fact(
            n=3,
            text="pipeline completeness: 4/5",
            citation=Citation(
                n=3,
                source_kind="computed",
                source_id="pc",
                retrieval_field="completeness",
            ),
        ),
    ]
    bundle.best_guess_allowed = best_guess
    return bundle


def test_synthesis_happy_path():
    bundle = _bundle()
    client = _MockAnthropic(
        ["An Ur III tablet from Drehem [1][2]. Pipeline 4/5 complete [3]."]
    )
    result = synthesize_artifact_summary(client, bundle, focus="general")
    assert client.calls == 1
    assert result.retried is False
    assert result.cited_ns == [1, 2, 3]
    assert len(result.citations) == 3


def test_synthesis_retry_succeeds():
    bundle = _bundle()
    client = _MockAnthropic(
        [
            # First attempt: unknown citation
            "An Ur III tablet from Drehem [99].",
            # Second attempt: valid
            "An Ur III tablet from Drehem [1][2]. Pipeline 4/5 [3].",
        ]
    )
    result = synthesize_artifact_summary(client, bundle, focus="general")
    assert client.calls == 2
    assert result.retried is True


def test_synthesis_two_failures_raises():
    bundle = _bundle()
    client = _MockAnthropic(
        [
            "Bad text [99].",
            "Still bad [99].",
        ]
    )
    with pytest.raises(SynthesisGroundingError):
        synthesize_artifact_summary(client, bundle, focus="general")


def test_synthesis_rejects_hypothesis_when_not_allowed():
    bundle = _bundle(best_guess=False)
    client = _MockAnthropic(
        [
            # Has hypothesis but bundle disallows it
            "An Ur III tablet [1]. (hypothesis) Resembles silver tablets [2][3].",
            # Retry with proper text
            "An Ur III tablet from Drehem [1][2]. Pipeline 4/5 [3].",
        ]
    )
    result = synthesize_artifact_summary(client, bundle, focus="general")
    assert result.retried is True
