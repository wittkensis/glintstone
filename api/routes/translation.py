"""REST: POST /api/v1/artifacts/{p_number}/lines/{line_id}/suggest-translation

Claude-assisted single-line translation aide for scholars (#531, PRD Phase 2).

This is the POST/body variant of the read-only GET in routes/agent.py
(suggest_line). It exists for the scholar workbench: the caller hands us a
specific ATF line (possibly an edit-in-progress not yet persisted), optional
surrounding context, a free-text note, and a confidence floor, and gets back a
ranked translation proposal.

Trust contract (CLAUDE.md):
- Source attribution is structural. Every call mints a fresh annotation_runs row
  (source_type='model', method='model') and returns its id, so any downstream
  use of the suggestion is provenance-linked to the run that produced it. We
  never overwrite a previous run.
- Competing interpretations are a feature: we return ranked alternatives, not a
  single verdict.

Two-tier rule: the web app calls this over HTTP; it never touches the DB
directly. Auth: same as other protected routes — the API key (glst_… header) is
resolved by AuthMiddleware into request.state.user, enforced here via
require_user.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel, Field

from api.dependencies import require_user
from api.prompts import line_translation
from core.agent.anthropic_client import AnthropicClient
from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/artifacts", tags=["translation"])


# ── Rate limiting ──────────────────────────────────────────────────────────────
# Simple in-memory fixed-window limiter: max N calls per window per client IP.
# Intentionally not Redis (#531 scope) — a single-process guardrail against an
# accidental hot loop, not a distributed quota. State is per-process; it resets
# on restart and is not shared across workers. A lock keeps the dict consistent
# under the threadpool FastAPI runs sync routes on.

_RATE_LIMIT_MAX = 10  # calls
_RATE_LIMIT_WINDOW_S = 60.0  # per this many seconds, per IP
_rate_lock = Lock()
_rate_buckets: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> None:
    """Raise 429 if client_ip has exceeded the window. Records the call if not."""
    now = time.monotonic()
    cutoff = now - _RATE_LIMIT_WINDOW_S
    with _rate_lock:
        hits = [t for t in _rate_buckets[client_ip] if t > cutoff]
        if len(hits) >= _RATE_LIMIT_MAX:
            _rate_buckets[client_ip] = hits
            retry_after = int(_RATE_LIMIT_WINDOW_S - (now - hits[0])) + 1
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit exceeded: max {_RATE_LIMIT_MAX} translation "
                    f"suggestions per {int(_RATE_LIMIT_WINDOW_S)}s."
                ),
                headers={"Retry-After": str(max(retry_after, 1))},
            )
        hits.append(now)
        _rate_buckets[client_ip] = hits


# ── Schemas ─────────────────────────────────────────────────────────────────────


class SuggestTranslationRequest(BaseModel):
    atf_line: str = Field(..., description="The ATF line to translate (with or without its line label).")
    context_lines: list[str] = Field(
        default_factory=list,
        description="Lines immediately before/after, for disambiguation.",
    )
    scholar_notes: str | None = Field(
        default=None, description="Optional free-text note from the scholar."
    )
    confidence_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Floor; suggestions below this are flagged low-confidence.",
    )


class SuggestTranslationResponse(BaseModel):
    suggestion: str
    confidence: float
    alternatives: list[str]
    reasoning: str
    annotation_run_id: str
    sources_consulted: list[str]
    below_threshold: bool = False


# ── DB helpers ───────────────────────────────────────────────────────────────────


def _line_exists(conn, p_number: str, line_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM text_lines WHERE id = %s AND p_number = %s",
            (line_id, p_number),
        )
        return cur.fetchone() is not None


def _fetch_lemma_readings(conn, line_id: int) -> list[dict]:
    """Existing lemma readings (norm + pos) for the tokens on this line.

    lemmatizations.token_id → tokens.id → tokens.line_id = line_id. Multiple
    scholars may have lemmatized the same token differently; we keep them all
    (competing interpretations are a feature) ordered by token position so the
    model sees the line left-to-right.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t."position" AS position, l.norm, l.pos
            FROM lemmatizations l
            JOIN tokens t ON t.id = l.token_id
            WHERE t.line_id = %s
              AND (l.norm IS NOT NULL OR l.pos IS NOT NULL)
            ORDER BY t."position" NULLS LAST, l.id
            """,
            (line_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def _fetch_scholar_corrections(conn, p_number: str) -> list[str]:
    """Recorded scholar corrections for this artifact's summary/interpretations.

    scholar_corrections targets are polymorphic: target_type='summary' is keyed
    by p_number; 'interpretation' is keyed by a token id. We surface accepted or
    pending summary-level corrections for this p_number — the line-level note the
    scholar passes in the request body is handled separately.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT correction_text
            FROM scholar_corrections
            WHERE target_type = 'summary'
              AND target_id = %s
              AND status IN ('pending', 'reviewed', 'accepted')
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (p_number,),
        )
        return [row["correction_text"] for row in cur.fetchall()]


def _create_annotation_run(conn, p_number: str, line_id: int, model_version: str) -> int:
    """Mint a fresh annotation_runs row for this suggestion (attribution).

    source_type='model' / method='model' satisfy the baseline CHECK constraints.
    Returns the new integer id. Committed by the caller alongside the rest of the
    request so a failed call leaves no orphan run.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO annotation_runs (source_type, source_name, method, model_version, notes)
            VALUES ('model', 'suggest_line_translation', 'model', %s, %s)
            RETURNING id
            """,
            (model_version, f"line suggestion for {p_number} line_id={line_id}"),
        )
        return cur.fetchone()["id"]


# ── LLM parse ────────────────────────────────────────────────────────────────────


def _parse_model_json(text: str) -> dict:
    """Parse the model's JSON object, tolerating ```json fences / surrounding prose."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1]
        if s.lstrip().lower().startswith("json"):
            s = s.lstrip()[4:]
        s = s.strip().rstrip("`").strip()
    # Fall back to slicing the outermost braces if there's stray prose.
    if not s.startswith("{"):
        lo, hi = s.find("{"), s.rfind("}")
        if lo != -1 and hi != -1 and hi > lo:
            s = s[lo : hi + 1]
    return json.loads(s)


# ── Route ────────────────────────────────────────────────────────────────────────


@router.post(
    "/{p_number}/lines/{line_id}/suggest-translation",
    response_model=SuggestTranslationResponse,
    summary="Claude-assisted translation proposal for a single ATF line (#531)",
)
def suggest_line_translation(
    request: Request,
    body: SuggestTranslationRequest,
    p_number: Annotated[str, Path()],
    line_id: Annotated[int, Path()],
    user: dict = Depends(require_user),
    conn=Depends(get_db),
) -> SuggestTranslationResponse:
    # 1. Rate limit by client IP (in-memory, per-process).
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    # 2. Validate the line belongs to the artifact (clear 404 over a silent empty result).
    if not _line_exists(conn, p_number, line_id):
        raise HTTPException(
            status_code=404,
            detail=f"line_id {line_id} not found on artifact {p_number}",
        )

    # 3. Gather grounding evidence.
    lemma_readings = _fetch_lemma_readings(conn, line_id)
    scholar_corrections = _fetch_scholar_corrections(conn, p_number)

    sources_consulted: list[str] = []
    if lemma_readings:
        sources_consulted.append("lemmatizations")
    if scholar_corrections:
        sources_consulted.append("scholar_corrections")

    # 4. Build the prompt and call Claude.
    user_message = line_translation.build_user_message(
        atf_line=body.atf_line,
        context_lines=body.context_lines,
        lemma_readings=lemma_readings,
        scholar_notes=body.scholar_notes,
        scholar_corrections=scholar_corrections,
    )

    try:
        anthropic = AnthropicClient()
        result = anthropic.complete(
            system_prompt=line_translation.SYSTEM_PROMPT,
            user_message=user_message,
        )
    except RuntimeError as exc:
        # Missing API key — surface as 503, not a 500 stack trace.
        logger.error("suggest_line_translation: anthropic unavailable: %r", exc)
        raise HTTPException(
            status_code=503, detail="Translation model is not configured."
        ) from exc
    except Exception as exc:  # network / API error
        logger.error("suggest_line_translation: anthropic call failed: %r", exc)
        raise HTTPException(
            status_code=502, detail="Translation model call failed."
        ) from exc

    try:
        parsed = _parse_model_json(result.text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error(
            "suggest_line_translation: unparseable model output: %r // %s",
            exc,
            result.text[:500],
        )
        raise HTTPException(
            status_code=502, detail="Translation model returned malformed output."
        ) from exc

    suggestion = str(parsed.get("suggestion", "")).strip()
    try:
        confidence = float(parsed.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    alternatives = [str(a) for a in (parsed.get("alternatives") or [])]
    reasoning = str(parsed.get("reasoning", "")).strip()

    # 5. Mint the annotation run (attribution is structural) and commit.
    run_id = _create_annotation_run(conn, p_number, line_id, result.model)
    conn.commit()

    logger.info(
        "suggest_line_translation p=%s line=%d run=%d conf=%.2f cache_hit=%s",
        p_number,
        line_id,
        run_id,
        confidence,
        result.cache_hit,
    )

    return SuggestTranslationResponse(
        suggestion=suggestion,
        confidence=confidence,
        alternatives=alternatives,
        reasoning=reasoning,
        # annotation_runs.id is integer in the baseline schema; the contract
        # types it as a string, so we stringify the integer id.
        annotation_run_id=str(run_id),
        sources_consulted=sources_consulted,
        below_threshold=confidence < body.confidence_threshold,
    )
