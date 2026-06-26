"""Admin routes — ingestion dashboard, dead-letter triage.

Queries v_ingestion_status (defined in migration 019) for the connector
overview and joins import_runs / import_dead_letters for detail views.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, Response

from core.database import get_connection

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(request: Request):
    """Return None if admin; return a Response to abort the handler."""
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse("/auth/login", status_code=302)
    try:
        user = request.app.state.api.get("/auth/me", token=token)
    except Exception:
        return RedirectResponse("/auth/login", status_code=302)
    if user.get("role") != "admin":
        return Response(status_code=403, content="Admin access required")
    return None


@router.get("/scholar-claims")
def scholar_claims_queue(request: Request, status: str = "pending"):
    """Admin review queue for scholar claims (#17). Admin-gated; the data comes
    from the API's admin router over HTTP (two-tier — this page never touches the
    DB). Filter pills switch the status feed."""
    guard = _require_admin(request)
    if guard is not None:
        return guard

    if status not in ("pending", "approved", "rejected"):
        status = "pending"
    token = request.cookies.get("session_token")
    try:
        data = request.app.state.api.list_admin_scholar_claims(status, token)
    except Exception:
        data = {
            "items": [],
            "counts": {"pending": 0, "approved": 0, "rejected": 0},
            "status": status,
        }

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "admin/scholar_claims.html",
        {
            "claims": data.get("items", []),
            "counts": data.get("counts", {}),
            "status": status,
        },
    )


@router.get("/scholar-corrections")
def scholar_corrections_queue(request: Request, status: str = "pending"):
    """Admin review queue for Level 2 scholar corrections (#532). Admin-gated;
    data comes from the API's admin router over HTTP (two-tier — this page never
    touches the DB). Filter pills switch the status feed."""
    guard = _require_admin(request)
    if guard is not None:
        return guard

    if status not in ("pending", "reviewed", "accepted", "rejected"):
        status = "pending"
    token = request.cookies.get("session_token")
    try:
        data = request.app.state.api.list_admin_scholar_corrections(status, token)
    except Exception:
        data = {
            "items": [],
            "counts": {"pending": 0, "reviewed": 0, "accepted": 0, "rejected": 0},
            "status": status,
        }

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "admin/scholar_corrections.html",
        {
            "corrections": data.get("items", []),
            "counts": data.get("counts", {}),
            "status": status,
        },
    )


@router.get("/ingestion")
def ingestion_dashboard(request: Request):
    """Connector overview: last run, status, open dead-letter count."""
    guard = _require_admin(request)
    if guard is not None:
        return guard
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM v_ingestion_status
            ORDER BY
                CASE last_run_status
                    WHEN 'failed' THEN 0
                    WHEN 'running' THEN 1
                    WHEN 'succeeded' THEN 2
                    WHEN 'no_op' THEN 3
                    ELSE 4 END,
                last_run_at DESC NULLS LAST,
                connector_id
            """
        ).fetchall()
        recent_runs = conn.execute(
            """
            SELECT id, connector_id, run_mode, started_at, finished_at,
                   status, rows_inserted, rows_dead_lettered, duration_ms
            FROM import_runs
            ORDER BY started_at DESC
            LIMIT 25
            """
        ).fetchall()
        dead_letter_summary = conn.execute(
            """
            SELECT connector_id, category, subcategory, COUNT(*) AS n
            FROM import_dead_letters
            WHERE resolution_status = 'open'
            GROUP BY connector_id, category, subcategory
            ORDER BY n DESC
            """
        ).fetchall()

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "admin/ingestion.html",
        {
            "connectors": [dict(r) for r in rows],
            "recent_runs": [dict(r) for r in recent_runs],
            "dead_letter_summary": [dict(r) for r in dead_letter_summary],
        },
    )


@router.get("/ingestion/{connector_id}")
def connector_detail(request: Request, connector_id: str):
    """Per-connector view: full run history and open dead-letter queue."""
    guard = _require_admin(request)
    if guard is not None:
        return guard
    with get_connection() as conn:
        source = conn.execute(
            "SELECT * FROM sources WHERE id = %s",
            (connector_id,),
        ).fetchone()
        if not source:
            raise HTTPException(
                status_code=404, detail=f"Unknown connector: {connector_id}"
            )
        runs = conn.execute(
            """
            SELECT id, run_mode, started_at, finished_at, status,
                   rows_seen, rows_inserted, rows_updated, rows_skipped,
                   rows_dead_lettered, duration_ms, error_summary
            FROM import_runs
            WHERE connector_id = %s
            ORDER BY started_at DESC
            LIMIT 50
            """,
            (connector_id,),
        ).fetchall()
        dead_letters = conn.execute(
            """
            SELECT id, run_id, category, subcategory, source_key, reason,
                   resolution_status, created_at
            FROM import_dead_letters
            WHERE connector_id = %s AND resolution_status = 'open'
            ORDER BY created_at DESC
            LIMIT 100
            """,
            (connector_id,),
        ).fetchall()

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "admin/connector_detail.html",
        {
            "source": dict(source),
            "runs": [dict(r) for r in runs],
            "dead_letters": [dict(r) for r in dead_letters],
        },
    )
