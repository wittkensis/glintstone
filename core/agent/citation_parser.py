"""Parse [n] markers from synthesis output and validate against the fact list.

See `.claude/skills/gs-expert-agentic/citation-contract.md` for the contract.

Two checks:
1. Every [n] in the text exists in the fact list. Unknown ns → reject.
2. Every sentence that makes a factual claim has at least one [n]. Uncited
   factual claims → reject.

The "is this a factual claim?" heuristic is intentionally simple. False
positives just trigger one retry; false negatives are caught by readers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_MARKER_RE = re.compile(r"\[(\d+)\]")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
# Factual-claim heuristic: a sentence with a noun-like token AND a copula or
# attribution verb. Cheap and good enough.
_CLAIM_VERB_RE = re.compile(
    r"\b(is|are|was|were|has|have|had|mentions?|cites?|contains?|references?|records?|describes?)\b",
    re.I,
)
_HYPOTHESIS_MARKER_RE = re.compile(r"\(hypothesis\)", re.I)
# Guard rail: hypothesis sentences must use 'resembles' / 'consistent with' /
# 'looks like' / 'may correspond to' / 'the candidate reading' — never 'is X' / 'means X'.
_HYPOTHESIS_FORBIDDEN_RE = re.compile(r"\b(is|means|refers to)\b", re.I)
_HYPOTHESIS_ALLOWED_RE = re.compile(
    r"\b(resembles?|consistent with|looks like|may correspond to|the candidate reading)\b",
    re.I,
)


@dataclass
class ValidationResult:
    ok: bool
    complaint: str = ""
    unknown_ns: list[int] | None = None
    uncited_sentences: list[str] | None = None


def extract_marker_ns(text: str) -> list[int]:
    return [int(m) for m in _MARKER_RE.findall(text)]


def validate(
    text: str, valid_ns: set[int], best_guess_allowed: bool
) -> ValidationResult:
    """Run all checks; return first failure or ok."""

    # 1. Unknown ns
    marker_ns = set(extract_marker_ns(text))
    unknown = sorted(marker_ns - valid_ns)
    if unknown:
        return ValidationResult(
            ok=False,
            complaint=(
                f"You cited {unknown} but those numbers are not in the FACTS list. "
                f"Only cite numbers shown in FACTS. Re-write using valid citations only."
            ),
            unknown_ns=unknown,
        )

    # 2. Hypothesis-section policy
    hypothesis_sentences: list[str] = []
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]

    for s in sentences:
        if _HYPOTHESIS_MARKER_RE.search(s):
            hypothesis_sentences.append(s)

    if hypothesis_sentences and not best_guess_allowed:
        return ValidationResult(
            ok=False,
            complaint=(
                "You included a (hypothesis) sentence but the input did not contain "
                "[BEST_GUESS]. Remove the hypothesis section."
            ),
        )

    # 3. Guard rail on hypothesis phrasing
    for h in hypothesis_sentences:
        stripped = _HYPOTHESIS_MARKER_RE.sub("", h)
        # Forbidden words OK if also accompanied by an allowed-phrase
        # (e.g. "Resembles X. It is consistent with Y." is fine; "It is X." is not.)
        if _HYPOTHESIS_FORBIDDEN_RE.search(
            stripped
        ) and not _HYPOTHESIS_ALLOWED_RE.search(stripped):
            return ValidationResult(
                ok=False,
                complaint=(
                    "Hypothesis sentences must use 'resembles', 'consistent with', "
                    "'looks like', 'may correspond to', or 'the candidate reading' — "
                    "never 'is X' or 'means X'."
                ),
            )

    # 4. Length
    if len(sentences) > 5:
        return ValidationResult(
            ok=False,
            complaint=f"Output is {len(sentences)} sentences. Maximum is 5.",
        )

    # 5. Uncited factual claims (skip hypothesis sentences — they cite via
    # evidence_chain in the citation_chain payload)
    uncited: list[str] = []
    for s in sentences:
        if _HYPOTHESIS_MARKER_RE.search(s):
            # Hypothesis sentences still need a citation, but the guard rail
            # already verified phrasing; require ≥1 marker
            if not _MARKER_RE.search(s):
                uncited.append(s)
            continue
        if _CLAIM_VERB_RE.search(s) and not _MARKER_RE.search(s):
            uncited.append(s)

    if uncited:
        return ValidationResult(
            ok=False,
            complaint=(
                f"These sentences make factual claims without [n] citations: "
                f"{uncited[:3]}. Add citations or remove the claims."
            ),
            uncited_sentences=uncited,
        )

    return ValidationResult(ok=True)


class SynthesisGroundingError(RuntimeError):
    """Raised when validation fails twice in a row.

    The caller should return a degraded ToolResponse (summary from structured
    facts, no synthesis) and log the failure to agent_interactions for review.
    """

    def __init__(self, last_complaint: str, last_text: str) -> None:
        super().__init__(f"Synthesis grounding failed: {last_complaint}")
        self.last_complaint = last_complaint
        self.last_text = last_text
