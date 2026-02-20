"""GET /stats — KPI and aggregate metrics."""

from fastapi import APIRouter, Depends

from core.database import get_db
from api.repositories.stats_repo import StatsRepository

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/kpi")
def get_kpi(conn=Depends(get_db)):
    repo = StatsRepository(conn)
    return repo.get_kpi()
