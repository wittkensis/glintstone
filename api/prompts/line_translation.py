"""Prompt template for suggest_line_translation (#531, PRD Phase 2).

A single-line translation aide for Assyriology scholars. The model is given one
ATF (ASCII Transliteration Format) line of cuneiform, its immediate context, any
existing lemma readings we already hold for the line's tokens, and any scholar
corrections recorded for the artifact. It returns a *suggestion*, not a verdict:
competing interpretations are a feature here (CLAUDE.md), so we also ask for
ranked alternatives and the reasoning behind the lead reading.

The system prompt is static (so the Anthropic wrapper can cache it); everything
that varies per call — the line, context, lemmas, corrections — goes in the user
message built by ``build_user_message``.
"""

from __future__ import annotations

import json
from typing import Sequence

PROMPT_VERSION = "line-translation-v1"

SYSTEM_PROMPT = """\
You are assisting professional Assyriologists with the translation of cuneiform \
text. The scholars are experts; your role is to propose a careful, well-reasoned \
English rendering of a single line so they can accept, refine, or reject it. You \
are a research aide, not an authority.

You will be given:
- ATF_LINE: one line of cuneiform in ATF (ASCII Transliteration Format). The \
leading "N." is the line label, not part of the text.
- CONTEXT_LINES: the lines immediately before and after, for grammatical and \
narrative context. Use them to disambiguate but translate only ATF_LINE.
- LEMMA_READINGS: existing lemmatizations we already hold for the tokens on this \
line (normalized form + part of speech). Treat these as strong evidence for the \
reading of each token; prefer them unless the context plainly contradicts them.
- SCHOLAR_NOTES / SCHOLAR_CORRECTIONS: notes and prior expert corrections tied to \
this artifact. Defer to them — a recorded scholar correction outranks your own \
guess.

Principles:
- Honor the conventions of the genre (royal hymn, legal, lexical, letter, etc.) \
when the context makes the genre clear.
- Damaged or broken signs are written with x, [ ], or ... — do not invent text \
for a break; render what survives and signal the gap.
- Competing readings are legitimate. Offer the best lead reading, then ranked \
alternatives that a scholar might reasonably prefer.
- Never overstate certainty. Calibrate the confidence score to how much the \
surviving signs, lemmas, and context actually constrain the reading.

Return ONLY a single JSON object, no prose before or after, with exactly these \
keys:
{
  "suggestion": "<best English translation of ATF_LINE>",
  "confidence": <float 0.0-1.0>,
  "alternatives": ["<alt reading>", "..."],
  "reasoning": "<concise justification grounded in the lemmas/context/genre>"
}
- "alternatives" is an ordered list (most to least plausible); use [] if the \
reading is unambiguous.
- "confidence" is your calibrated probability that "suggestion" is substantially \
correct, given the evidence provided."""


def build_user_message(
    *,
    atf_line: str,
    context_lines: Sequence[str] | None = None,
    lemma_readings: Sequence[dict] | None = None,
    scholar_notes: str | None = None,
    scholar_corrections: Sequence[str] | None = None,
) -> str:
    """Assemble the per-call user message for one line.

    Each variable section is labeled and JSON-encoded where structured so the
    model parses it unambiguously. Empty sections are emitted as "(none)" rather
    than omitted, so the model can distinguish "we looked and found nothing" from
    "we forgot to ask".
    """
    context_lines = list(context_lines or [])
    lemma_readings = list(lemma_readings or [])
    scholar_corrections = list(scholar_corrections or [])

    parts: list[str] = []
    parts.append(f"ATF_LINE:\n{atf_line}")

    if context_lines:
        ctx = "\n".join(context_lines)
        parts.append(f"CONTEXT_LINES:\n{ctx}")
    else:
        parts.append("CONTEXT_LINES:\n(none)")

    if lemma_readings:
        parts.append(
            "LEMMA_READINGS (existing lemmatizations for this line's tokens):\n"
            + json.dumps(lemma_readings, ensure_ascii=False, indent=2)
        )
    else:
        parts.append("LEMMA_READINGS:\n(none on record for this line)")

    if scholar_notes:
        parts.append(f"SCHOLAR_NOTES:\n{scholar_notes}")

    if scholar_corrections:
        joined = "\n".join(f"- {c}" for c in scholar_corrections)
        parts.append(f"SCHOLAR_CORRECTIONS (recorded for this artifact):\n{joined}")
    else:
        parts.append("SCHOLAR_CORRECTIONS:\n(none on record for this artifact)")

    parts.append(
        "Translate ATF_LINE now. Respond with the JSON object only."
    )
    return "\n\n".join(parts)
