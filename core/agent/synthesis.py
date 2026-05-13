"""Grounded synthesis loop.

Pipeline:
  1. assemble_facts() builds list[Fact] with citations
  2. Render facts to numbered prompt block
  3. Call Claude (cached system prompt)
  4. Validate [n] markers via citation_parser
  5. Retry once on failure with validator complaint appended
  6. Return SynthesisResult OR raise SynthesisGroundingError

See `.claude/skills/gs-expert-agentic/citation-contract.md` and `prompts/`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from core.agent.anthropic_client import AnthropicClient, CompletionResult
from core.agent.citation_parser import (
    SynthesisGroundingError,
    extract_marker_ns,
    validate,
)
from core.agent.fact_assembly import ArtifactFactBundle, Fact, TokenFactBundle
from core.schemas.citation import Citation

logger = logging.getLogger(__name__)


_PROMPTS_DIR = (
    Path(__file__).resolve().parents[2] / ".claude/skills/gs-expert-agentic/prompts"
)


@dataclass
class SynthesisResult:
    text: str  # text with [n] markers preserved
    cited_ns: list[int]  # only ns that actually appeared
    citations: list[Citation]  # filtered to those cited
    prompt_version: str  # filename stem
    completion: CompletionResult
    retried: bool


def _load_prompt(version: str) -> str:
    """Load the bare system prompt from prompts/<version>.md.

    The file is markdown with a YAML header and a <system>...</system> block.
    We extract everything between the <system> tags.
    """
    path = _PROMPTS_DIR / f"{version}.md"
    text = path.read_text(encoding="utf-8")
    start = text.find("<system>")
    end = text.find("</system>")
    if start < 0 or end < 0:
        raise RuntimeError(f"Prompt file {path} missing <system>...</system> block")
    return text[start + len("<system>") : end].strip()


def _render_facts(facts: list[Fact]) -> str:
    return "FACTS:\n" + "\n".join(f"[{f.n}] {f.text}" for f in facts)


def _render_similar(similar_block_text: str | None) -> str:
    return ("\n\n" + similar_block_text) if similar_block_text else ""


def _filter_cited(text: str, facts: list[Fact]) -> tuple[list[int], list[Citation]]:
    cited_set = set(extract_marker_ns(text))
    fact_by_n = {f.n: f for f in facts}
    cited_ns = sorted(cited_set)
    citations = [fact_by_n[n].citation for n in cited_ns if n in fact_by_n]
    return cited_ns, citations


# ── Public entry points ───────────────────────────────────────────────────────


def synthesize_artifact_summary(
    client: AnthropicClient,
    bundle: ArtifactFactBundle,
    focus: str = "general",
    prompt_version: str = "synthesis.v1",
) -> SynthesisResult:
    """Run the grounded synthesis loop for summarize_artifact."""
    system_prompt = _load_prompt(prompt_version)

    similar_block = ""
    if bundle.similar_tablets:
        similar_block = "SIMILAR TABLETS:\n" + "\n".join(
            f"[{st.n}] {st.p_number} — "
            f"{st.period or 'unknown period'}, "
            f"{st.provenience or 'unknown provenience'}"
            for st in bundle.similar_tablets
        )

    user_message_base = (
        _render_facts(bundle.facts)
        + _render_similar(similar_block)
        + f"\n\nINTENT: {focus}"
    )
    if bundle.best_guess_allowed:
        user_message_base += "\n[BEST_GUESS]"

    return _run_loop(
        client=client,
        system_prompt=system_prompt,
        user_message_base=user_message_base,
        facts=bundle.facts,
        best_guess_allowed=bundle.best_guess_allowed,
        prompt_version=prompt_version,
    )


def synthesize_token_interpretation(
    client: AnthropicClient,
    bundle: TokenFactBundle,
    prompt_version: str = "interpret-token.v1",
) -> SynthesisResult:
    """Run the grounded synthesis loop for interpret_token.

    Note: the interpret-token prompt asks for JSON output. The caller
    (api/services/agent.py) parses the JSON; this function just runs the
    Claude loop and surface-validates markers.
    """
    system_prompt = _load_prompt(prompt_version)

    user_message_base = _render_facts(bundle.facts) + "\n\nINTENT: interpret"

    # For interpret-token, the [n] markers live inside JSON fact_refs arrays.
    # The text-level validator works the same way — it just scans the raw
    # output text for [n] occurrences. The caller can additionally JSON-parse.
    return _run_loop(
        client=client,
        system_prompt=system_prompt,
        user_message_base=user_message_base,
        facts=bundle.facts,
        best_guess_allowed=True,  # token interpretation always allows hypotheses
        prompt_version=prompt_version,
        max_tokens=3072,
    )


# ── Inner loop ────────────────────────────────────────────────────────────────


def _run_loop(
    client: AnthropicClient,
    system_prompt: str,
    user_message_base: str,
    facts: list[Fact],
    best_guess_allowed: bool,
    prompt_version: str,
    max_tokens: int = 2048,
) -> SynthesisResult:
    valid_ns = {f.n for f in facts}
    user_message = user_message_base

    for attempt in range(2):
        completion = client.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
        )
        text = completion.text

        # For JSON-output prompts (interpret-token), we still validate the
        # [n] markers using the same heuristic. JSON braces don't trip the
        # marker regex.
        result = validate(text, valid_ns, best_guess_allowed=best_guess_allowed)
        if result.ok:
            cited_ns, citations = _filter_cited(text, facts)
            return SynthesisResult(
                text=text,
                cited_ns=cited_ns,
                citations=citations,
                prompt_version=prompt_version,
                completion=completion,
                retried=(attempt == 1),
            )

        # Append the validator's complaint and retry
        logger.warning(
            "synthesis validation failed (attempt %d/2): %s",
            attempt + 1,
            result.complaint,
        )
        user_message = (
            user_message_base
            + "\n\nYour previous response was:\n"
            + text
            + "\n\nProblem with that response: "
            + result.complaint
            + "\n\nRe-write following the GROUNDING RULES exactly."
        )

    raise SynthesisGroundingError(
        last_complaint=result.complaint,
        last_text=completion.text,
    )
