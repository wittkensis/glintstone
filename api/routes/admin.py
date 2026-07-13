"""Admin API routes — scholar-claim review queue + verification (#17).

These are the admin-gated half of the Scholar Identity feature. The web app's
admin pages proxy to these over HTTP (two-tier rule). Every route requires the
``admin`` role via ``require_admin`` — a standard user hitting them gets 403.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import logging

from api.dependencies import require_admin
from api.services import email_service
from core.config import get_settings
from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class VerifyClaimRequest(BaseModel):
    action: str  # 'approve' | 'reject'
    review_note: str | None = None


@router.get("/scholar-claims")
def list_scholar_claims(
    status: str = "pending",
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """The review queue feed. Default ``status=pending`` (oldest first, so the
    longest-waiting claimant is reviewed first). ``approved`` / ``rejected``
    filters show the audit trail (who acted, when). Each row carries the user
    (email/name/orcid) and the scholar (name/institution/pub count) so the
    reviewer has full context in one screen.
    """
    if status not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status filter")

    order = (
        "c.claimed_at ASC" if status == "pending" else "c.verified_at DESC NULLS LAST"
    )
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT c.id, c.scholar_id, c.status, c.verification_method,
                   c.claim_note, c.claimed_at, c.verified_at, c.review_note,
                   u.id AS user_id, u.email AS user_email,
                   u.display_name AS user_display_name, u.orcid_id AS user_orcid,
                   s.name AS scholar_name, s.institution AS scholar_institution,
                   (SELECT COUNT(*) FROM publication_authors pa
                     WHERE pa.scholar_id = s.id) AS scholar_publication_count,
                   v.display_name AS verified_by_name
            FROM scholar_claims c
            JOIN users u    ON u.id = c.user_id
            JOIN scholars s ON s.id = c.scholar_id
            LEFT JOIN users v ON v.id = c.verified_by
            WHERE c.status = %s
            ORDER BY {order}
            """,
            (status,),
        )
        rows = cur.fetchall()

        # Counts for the filter pills (always all three, regardless of filter).
        cur.execute("SELECT status, COUNT(*) AS n FROM scholar_claims GROUP BY status")
        counts = {r["status"]: int(r["n"]) for r in cur.fetchall()}

    return {
        "items": [dict(r) for r in rows],
        "counts": {
            "pending": counts.get("pending", 0),
            "approved": counts.get("approved", 0),
            "rejected": counts.get("rejected", 0),
        },
        "status": status,
    }


@router.post("/scholar-claims/{claim_id}/verify")
def verify_scholar_claim(
    claim_id: str,
    body: VerifyClaimRequest,
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """Approve or reject a pending claim.

    Approve → status='approved', stamps verified_at/verified_by, and creates the
    empty ``scholar_overrides`` shell so the claimant's bio editor is immediately
    available. The partial unique index enforces one approved claim per scholar:
    a second approval on an already-claimed scholar raises 409 rather than
    silently double-claiming.

    Reject → status='rejected' with a REQUIRED review_note (shown back to the
    claimant on their /account page). Two-step in the UI; required here so a
    reject never reaches the user with no explanation.
    """
    action = body.action.strip().lower()
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be approve or reject")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.scholar_id, c.user_id, c.status,
                   u.email AS user_email, s.name AS scholar_name
              FROM scholar_claims c
              JOIN users    u ON u.id = c.user_id
              JOIN scholars s ON s.id = c.scholar_id
             WHERE c.id = %s
            """,
            (claim_id,),
        )
        claim = cur.fetchone()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        if claim["status"] != "pending":
            raise HTTPException(
                status_code=409, detail="This claim has already been reviewed."
            )

        if action == "reject":
            note = (body.review_note or "").strip()
            if not note:
                raise HTTPException(
                    status_code=400,
                    detail="A reason is required when rejecting a claim.",
                )
            cur.execute(
                """
                UPDATE scholar_claims
                   SET status = 'rejected', review_note = %s,
                       verified_at = now(), verified_by = %s
                 WHERE id = %s
                """,
                (note, admin["id"], claim_id),
            )
            conn.commit()
            try:
                email_service.send_claim_rejected(
                    claim["user_email"], claim["scholar_name"], note, get_settings()
                )
            except Exception as exc:
                logger.error("Claim reject notification email failed: %s", exc)
            return {"status": "rejected"}

        # Approve — guard against an existing approved claim for this scholar so
        # the partial unique index never surprises us with a rollback-trap error.
        cur.execute(
            "SELECT 1 FROM scholar_claims "
            "WHERE scholar_id = %s AND status = 'approved'",
            (claim["scholar_id"],),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Another claim on this scholar is already approved.",
            )
        cur.execute(
            """
            UPDATE scholar_claims
               SET status = 'approved', verified_at = now(), verified_by = %s,
                   review_note = %s
             WHERE id = %s
            """,
            (admin["id"], (body.review_note or "").strip() or None, claim_id),
        )
        # Create the empty overlay shell. ON CONFLICT, not try/except (rollback trap).
        cur.execute(
            """
            INSERT INTO scholar_overrides (scholar_id, edited_by_user_id)
            VALUES (%s, %s)
            ON CONFLICT (scholar_id) DO NOTHING
            """,
            (claim["scholar_id"], claim["user_id"]),
        )
    conn.commit()
    try:
        email_service.send_claim_approved(
            claim["user_email"], claim["scholar_name"], get_settings()
        )
    except Exception as exc:
        logger.error("Claim approve notification email failed: %s", exc)
    return {"status": "approved"}
