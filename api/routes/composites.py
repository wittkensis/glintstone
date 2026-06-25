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
    conn=Depends(get_db),
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
            offset=offset,
        )
    else:
        composites = repo.find_all(limit=limit, offset=offset)

    total = repo.get_total_count()

    return {"items": composites, "total": total, "limit": limit, "offset": offset}


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

    # ATF preview (#159): the transliterated text of a representative exemplar,
    # shown inline on the composition detail page. None when no linked exemplar
    # carries readable ATF, so the page renders its #189 empty state.
    atf_preview = repo.get_representative_atf_preview(q_number)

    # Related compositions (#160): sibling texts that share a witness tablet.
    # Empty list when this composition shares no exemplar with any other — the
    # detail page omits the "Related compositions" widget in that case.
    related = repo.get_related_composites(q_number)

    return {
        "composite": composite,
        "exemplars": exemplars,
        "atf_preview": atf_preview,
        "related": related,
    }


@router.get("/{q_number}/related")
def get_composite_related(
    q_number: str,
    limit: int = Query(8, ge=1, le=24, description="Max related compositions"),
    conn=Depends(get_db),
):
    """Compositions related to this one by shared witnesses (#160).

    The relation is structural: a tablet linked to both compositions via
    ``artifact_composites``. Returns ``related: []`` for a composition with no
    shared witness (the UI omits the widget); 404 only for an unknown Q-number.
    See ``CompositeRepository.get_related_composites`` for the data-gate
    rationale (explicit-relation and genre/period signals are unavailable).
    """
    repo = CompositeRepository(conn)

    composite = repo.find_by_q_number(q_number)
    if not composite:
        raise HTTPException(status_code=404, detail=f"Composite {q_number} not found")

    return {
        "q_number": q_number,
        "related": repo.get_related_composites(q_number, limit=limit),
    }


@router.get("/{q_number}/atf-preview")
def get_composite_atf_preview(
    q_number: str,
    limit: int = Query(8, ge=1, le=40, description="Lines to preview"),
    conn=Depends(get_db),
):
    """Transliterated-text preview of a representative exemplar (#159).

    Picks the linked exemplar with the most readable ATF lines and returns its
    first ``limit`` lines verbatim (prime notation, damage brackets preserved).
    ``atf_preview`` is ``null`` for a composite with no readable-ATF exemplar
    (the page renders the #189 empty state); 404 only for an unknown Q-number.
    """
    repo = CompositeRepository(conn)

    composite = repo.find_by_q_number(q_number)
    if not composite:
        raise HTTPException(status_code=404, detail=f"Composite {q_number} not found")

    return {
        "q_number": q_number,
        "atf_preview": repo.get_representative_atf_preview(q_number, limit=limit),
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

    return {"q_number": q_number, "exemplars": exemplars, "count": len(exemplars)}


@router.get("/{q_number}/collation")
def get_composite_collation(
    q_number: str,
    max_witnesses: int = Query(default=6, ge=2, le=12),
    conn=Depends(get_db),
):
    """Line-aligned witness collation for a composition (#527).

    Aligns all witness tablets by (surface_type, line_number) — the same label
    used in ATF notation. Each row is one canonical line; each column is one
    witness. Only returned when 2–max_witnesses witnesses have at least one ATF
    line (otherwise the collation table is either trivial or too wide to render).

    Response shape::

        {
          "q_number": "Q001001",
          "witnesses": ["P226189", "P226190", ...],   # ordered by attestation count
          "rows": [
            {
              "surface": "obverse",
              "line_number": "1",
              "cells": {"P226189": "szu-suen", "P226190": "szu-suen", ...}
            },
            ...
          ],
          "witness_count": 4,
          "line_count": 10
        }

    Returns {"available": false} when fewer than 2 witnesses have ATF, so the
    caller can degrade gracefully without an error.
    """
    repo = CompositeRepository(conn)
    composite = repo.find_by_q_number(q_number)
    if not composite:
        raise HTTPException(status_code=404, detail=f"Composite {q_number} not found")

    with conn.cursor() as cur:
        # Witnesses with at least one ATF line, ordered by how many lines they
        # have (fullest witness first — typically the most complete exemplar).
        cur.execute(
            """
            SELECT ac.p_number,
                   COUNT(tl.id) AS line_count,
                   a.designation
            FROM artifact_composites ac
            JOIN artifacts a ON a.p_number = ac.p_number
            JOIN text_lines tl ON tl.p_number = ac.p_number
            WHERE ac.q_number = %s
              AND tl.is_ruling = 0
              AND tl.is_blank = 0
              AND tl.raw_atf IS NOT NULL
              AND tl.raw_atf != ''
            GROUP BY ac.p_number, a.designation
            ORDER BY line_count DESC
            LIMIT %s
            """,
            (q_number, max_witnesses),
        )
        witness_rows = cur.fetchall()

    if len(witness_rows) < 2:
        return {"q_number": q_number, "available": False}

    witnesses = [r["p_number"] for r in witness_rows]
    witness_meta = {r["p_number"]: r["designation"] for r in witness_rows}

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tl.p_number,
                   COALESCE(s.surface_type, 'tablet') AS surface,
                   tl.line_number,
                   tl.raw_atf
            FROM text_lines tl
            LEFT JOIN surfaces s ON s.id = tl.surface_id
            WHERE tl.p_number = ANY(%s)
              AND tl.is_ruling = 0
              AND tl.is_blank = 0
              AND tl.raw_atf IS NOT NULL
              AND tl.raw_atf != ''
            ORDER BY tl.p_number,
                     CASE s.surface_type
                         WHEN 'obverse' THEN 1 WHEN 'reverse' THEN 2
                         WHEN 'left_edge' THEN 3 WHEN 'right_edge' THEN 4
                         ELSE 5 END,
                     tl.line_number::int
            """,
            (witnesses,),
        )
        line_rows = cur.fetchall()

    # Build collation grid: key = (surface, line_number) → {p_number: atf}
    from collections import OrderedDict

    grid: dict = OrderedDict()
    for lr in line_rows:
        key = (lr["surface"], lr["line_number"])
        if key not in grid:
            grid[key] = {"surface": lr["surface"], "line_number": lr["line_number"], "cells": {}}
        grid[key]["cells"][lr["p_number"]] = lr["raw_atf"]

    rows = list(grid.values())

    return {
        "q_number": q_number,
        "available": True,
        "witnesses": witnesses,
        "witness_meta": witness_meta,
        "rows": rows,
        "witness_count": len(witnesses),
        "line_count": len(rows),
    }


@router.get("/{q_number}/witnesses/{p_number}/atf-preview")
def get_composite_witness_atf_preview(
    q_number: str,
    p_number: str,
    limit: int = Query(8, ge=1, le=40, description="Lines to preview"),
    conn=Depends(get_db),
):
    """First-N readable ATF lines of one specific witness (#404 Concept A).

    Backs the witness-switcher: clicking a witness chip on the composition page
    fetches *that* witness's text in place. ``atf_preview`` is ``null`` when the
    witness is not linked to this composite or carries no readable ATF (the
    client keeps the current preview); 404 only for an unknown Q-number.
    """
    repo = CompositeRepository(conn)

    composite = repo.find_by_q_number(q_number)
    if not composite:
        raise HTTPException(status_code=404, detail=f"Composite {q_number} not found")

    return {
        "q_number": q_number,
        "p_number": p_number,
        "atf_preview": repo.get_witness_atf_preview(q_number, p_number, limit=limit),
    }
