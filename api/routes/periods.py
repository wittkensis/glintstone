"""GET /periods — canonical historical periods with BCE date ranges.

Publicly served as /api/v2/periods (the nginx gateway prepends /api/v2/ to
the bare router prefix, same as every other API route). The transmission
timeline on composition detail pages fetches this to position exemplars on a
proportional BCE axis instead of equal-width buckets.
"""

from fastapi import APIRouter, Depends

from core.database import get_db
from api.repositories.period_repo import PeriodRepository

router = APIRouter(prefix="/periods", tags=["periods"])


@router.get("")
def list_periods(conn=Depends(get_db)):
    """Canonical periods ordered chronologically (by sort_order).

    Returns {"items": [{canonical, date_start_bce, date_end_bce,
    sort_order, group_name}, ...]}. date_start_bce / date_end_bce are
    negative integers (BCE) or null when a period has no agreed range.
    """
    repo = PeriodRepository(conn)
    return {"items": repo.get_canonical_periods()}
