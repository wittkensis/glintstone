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
import re
from dataclasses import dataclass
from pathlib import Path

from core.agent.anthropic_client import AnthropicClient, CompletionResult
from core.agent.citation_parser import (
    SynthesisGroundingError,
    ValidationResult,
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
    prompt_version: str = "synthesis.v2",
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
        run_v2_checks=prompt_version.startswith("synthesis.v2"),
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


# ── v2 semantic checks ────────────────────────────────────────────────────────

_RAW_DIALECT_RE = re.compile(r"\bakk-x-[a-z]+\b")
_MIXED_LANG_SIGNAL = "mixed language:"
_DISAGREEMENT_SIGNAL = "scholarly disagreement on"
_UNCERTAINTY_PHRASES_RE = re.compile(
    r"\b(disagree|contested|uncertain|scholars? read|reading of)\b", re.I
)


def _validate_v2_semantics(text: str, facts: list[Fact]) -> ValidationResult:
    """Extra checks for synthesis.v2 — only run when dialect/mixed/disagreement facts exist."""
    fact_texts = [f.text.lower() for f in facts]

    has_dialect_fact = any("akkadian dialect" in ft for ft in fact_texts)
    has_mixed_fact = any(_MIXED_LANG_SIGNAL in ft for ft in fact_texts)
    has_disagreement_fact = any(_DISAGREEMENT_SIGNAL in ft for ft in fact_texts)

    if has_dialect_fact and _RAW_DIALECT_RE.search(text):
        return ValidationResult(
            ok=False,
            complaint=(
                "Output contains a raw akk-x-* dialect code. Translate to the "
                "human-readable form (e.g. 'Old Babylonian Akkadian' for akk-x-oldbab). "
                "See dialect mapping in the system prompt."
            ),
        )

    if has_mixed_fact and not re.search(
        r"\b(sumerian|akkadian|bilingual|mixed|both languages?)\b", text, re.I
    ):
        return ValidationResult(
            ok=False,
            complaint=(
                "A 'mixed language' fact is in the FACTS list but the summary makes no "
                "mention of the bilingual or mixed-language character of the text. Address it."
            ),
        )

    if has_disagreement_fact and not _UNCERTAINTY_PHRASES_RE.search(text):
        return ValidationResult(
            ok=False,
            complaint=(
                "A 'scholarly disagreement' fact is in the FACTS list but the summary "
                "asserts the reading without qualification. Use phrases like "
                "'scholars disagree', 'the reading is contested', or 'possibly'."
            ),
        )

    return ValidationResult(ok=True)


# ── Inner loop ────────────────────────────────────────────────────────────────


def _run_loop(
    client: AnthropicClient,
    system_prompt: str,
    user_message_base: str,
    facts: list[Fact],
    best_guess_allowed: bool,
    prompt_version: str,
    max_tokens: int = 2048,
    run_v2_checks: bool = False,
) -> SynthesisResult:
    valid_ns = {f.n for f in facts}
    user_message = user_message_base
    result: ValidationResult | None = None

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
        if result.ok and run_v2_checks:
            result = _validate_v2_semantics(text, facts)
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

        # Retry: send only a brief excerpt of the failed output to avoid
        # flooding smaller models with a confusing blob of bad text.
        logger.warning(
            "synthesis validation failed (attempt %d/2): %s",
            attempt + 1,
            result.complaint,
        )
        failed_excerpt = text[:300] + ("…" if len(text) > 300 else "")
        user_message = (
            user_message_base
            + "\n\nYour previous response started: "
            + failed_excerpt
            + "\n\nProblem: "
            + result.complaint
            + "\n\nRe-write following the GROUNDING RULES exactly."
        )

    raise SynthesisGroundingError(
        last_complaint=result.complaint,
        last_text=completion.text,
    )
