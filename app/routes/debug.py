"""Internal debug UI for the agentic surface.

Gated by APP_DEBUG=true. Not in nav, never reachable from public site.
Three tabs:
  /_debug/agentic               → search inspector
  /_debug/agentic/summary       → artifact summary inspector
  /_debug/agentic/interpret     → token interpretation inspector
  /_debug/agentic/interactions  → recent agent_interactions log + agent_outputs history
  /_debug/agentic/corrections   → submit a correction (POST endpoint)

Lets Eric exercise every code path the agent uses, see raw ToolResponse JSON,
inspect citations, view source chains, and check the learning loop.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from core.config import get_settings
from core.database import get_connection

BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _ensure_debug_enabled() -> None:
    settings = get_settings()
    if not settings.app_debug:
        raise HTTPException(status_code=404, detail="not found")


router = APIRouter(prefix="/_debug/agentic", include_in_schema=False)


# ── Tab 1: search inspector ──────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
@router.get("/search", response_class=HTMLResponse)
def debug_search(request: Request, q: str | None = None, mode: str = "hybrid"):
    """Search tab."""
    _ensure_debug_enabled()
    response: dict | None = None
    error: str | None = None
    if q:
        try:
            response = request.app.state.api.get(
                "/search",
                params={"q": q, "mode": mode, "limit": 5},
            )
        except Exception as exc:
            error = str(exc)

    return templates.TemplateResponse(
        "_debug/agentic.html",
        {
            "request": request,
            "tab": "search",
            "q": q or "",
            "mode": mode,
            "response": response,
            "response_json": json.dumps(response, indent=2, default=str)
            if response
            else None,
            "error": error,
        },
    )


# ── Tab 2: summarize artifact inspector ──────────────────────────────────────


@router.get("/summary", response_class=HTMLResponse)
def debug_summary(
    request: Request, p_number: str | None = None, focus: str = "general"
):
    _ensure_debug_enabled()
    response: dict | None = None
    error: str | None = None
    if p_number:
        try:
            response = request.app.state.api.get(
                f"/artifacts/{p_number}/summary",
                params={"focus": focus},
            )
        except Exception as exc:
            error = str(exc)

    return templates.TemplateResponse(
        "_debug/agentic.html",
        {
            "request": request,
            "tab": "summary",
            "p_number": p_number or "",
            "focus": focus,
            "response": response,
            "response_json": json.dumps(response, indent=2, default=str)
            if response
            else None,
            "error": error,
        },
    )


# ── Tab 3: interpret token inspector ─────────────────────────────────────────


@router.get("/interpret", response_class=HTMLResponse)
def debug_interpret(
    request: Request,
    p_number: str | None = None,
    token_id: int | None = None,
):
    _ensure_debug_enabled()
    response: dict | None = None
    error: str | None = None
    if p_number and token_id:
        try:
            response = request.app.state.api.get(
                f"/artifacts/{p_number}/tokens/{token_id}/interpret",
            )
        except Exception as exc:
            error = str(exc)

    # Helpful: also let the user pick a token from the artifact
    token_candidates: list[dict] = []
    if p_number and not token_id:
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT t.id AS token_id, t.position, t.raw_form,
                               tl.line_number,
                               ll.id IS NOT NULL AS lemmatized
                        FROM tokens t
                        JOIN text_lines tl ON t.line_id = tl.id
                        JOIN surfaces s ON tl.surface_id = s.id
                        LEFT JOIN lemmatizations lz ON lz.token_id = t.id
                        LEFT JOIN lexical_lemmas ll ON ll.id = lz.lemma_id
                        WHERE s.p_number = %s
                        ORDER BY tl.line_number, t.position
                        LIMIT 50
                        """,
                        (p_number,),
                    )
                    token_candidates = cur.fetchall() or []
        except Exception as exc:
            error = (error + " | " if error else "") + f"token list: {exc}"

    return templates.TemplateResponse(
        "_debug/agentic.html",
        {
            "request": request,
            "tab": "interpret",
            "p_number": p_number or "",
            "token_id": token_id or "",
            "response": response,
            "response_json": json.dumps(response, indent=2, default=str)
            if response
            else None,
            "token_candidates": token_candidates,
            "error": error,
        },
    )


# ── Tab 4: agent_interactions log + agent_outputs history ────────────────────


@router.get("/interactions", response_class=HTMLResponse)
def debug_interactions(request: Request, limit: int = 50):
    _ensure_debug_enabled()
    interactions: list[dict] = []
    outputs: list[dict] = []
    error: str | None = None
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, surface, tool_name, route_path,
                           request, response_summary, result_ids, latency_ms,
                           error_code, client_label, created_at
                    FROM agent_interactions
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                interactions = cur.fetchall() or []

                cur.execute(
                    """
                    SELECT id, output_type, target_type, target_id, focus,
                           model, prompt_version, generated_at, superseded_at,
                           best_guess_flag,
                           LEFT(output_text, 200) AS output_preview
                    FROM agent_outputs
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                outputs = cur.fetchall() or []
    except Exception as exc:
        error = str(exc)

    return templates.TemplateResponse(
        "_debug/agentic.html",
        {
            "request": request,
            "tab": "interactions",
            "interactions": interactions,
            "outputs": outputs,
            "error": error,
        },
    )


# ── Correction form ──────────────────────────────────────────────────────────


@router.post("/correct", response_class=JSONResponse)
def debug_correct(
    request: Request,
    interaction_id: int = Form(...),
    claim: str = Form(...),
    correction: str = Form(...),
    scholar_id: int | None = Form(None),
    evidence: str | None = Form(None),
):
    _ensure_debug_enabled()
    try:
        result = request.app.state.api.post(
            "/agentic/corrections",
            json={
                "interaction_id": interaction_id,
                "claim": claim,
                "correction": correction,
                "scholar_id": scholar_id,
                "evidence": evidence,
            },
        )
        return JSONResponse(result)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
