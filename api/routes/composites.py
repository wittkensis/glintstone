"""
API routes for composite text data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from core.database import get_db
from api.repositories.composite_repo import CompositeRepository

router = APIRouter(prefix="/composites", tags=["composites"])


@router.get("")
def list_composites(
    language: str | None = Query(None, description="Filter by language"),
    period: str | None = Query(None, description="Filter by period"),
    genre: str | None = Query(None, description="Filter by genre"),
    search: str | None = Query(None, description="Search in designation"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    conn=Depends(get_db)
):
    """
    List all composites with optional filtering and pagination.

    Returns list of composite text metadata including Q-number, designation,
    language, period, genre, and exemplar count.
    """
    repo = CompositeRepository(conn)

    if any([language, period, genre, search]):
        composites = repo.search(
            language=language,
            period=period,
            genre=genre,
            search=search,
            limit=limit,
            offset=offset
        )
    else:
        composites = repo.find_all(limit=limit, offset=offset)

    total = repo.get_total_count()

    return {
        "items": composites,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{q_number}")
def get_composite(q_number: str, conn=Depends(get_db)):
    """
    Get detailed information about a specific composite by Q-number.

    Includes metadata and list of exemplar tablets.
    """
    repo = CompositeRepository(conn)

    composite = repo.find_by_q_number(q_number)
    if not composite:
        raise HTTPException(status_code=404, detail=f"Composite {q_number} not found")

    exemplars = repo.get_exemplars(q_number)

    return {
        "composite": composite,
        "exemplars": exemplars
    }


@router.get("/{q_number}/exemplars")
def get_composite_exemplars(q_number: str, conn=Depends(get_db)):
    """
    Get all exemplar tablets for a specific composite.

    Returns list of P-numbers and metadata for tablets that exemplify this composite.
    """
    repo = CompositeRepository(conn)

    # Verify composite exists
    composite = repo.find_by_q_number(q_number)
    if not composite:
        raise HTTPException(status_code=404, detail=f"Composite {q_number} not found")

    exemplars = repo.get_exemplars(q_number)

    return {
        "q_number": q_number,
        "exemplars": exemplars,
        "count": len(exemplars)
    }
