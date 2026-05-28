"""GET /stats — KPI and aggregate metrics."""

from fastapi import APIRouter, Depends

from core.database import get_db
from api.repositories.stats_repo import StatsRepository

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/kpi")
def get_kpi(conn=Depends(get_db)):
    repo = StatsRepository(conn)
    return repo.get_kpi()


@router.get("/coverage-gaps")
def get_coverage_gaps(min_exemplars: int = 5, limit: int = 4, conn=Depends(get_db)):
    """Compositions with the largest unattested line-ref gaps.

    Returns empty list when line_ref data is not yet populated (atf-parser
    connector must run first). Homepage hides the Frontier section gracefully.
    """
    repo = StatsRepository(conn)
    return {"items": repo.get_coverage_gaps(min_exemplars=min_exemplars, limit=limit)}
