"""Scholar routes — minimal listing + detail (read-only).

Scholars are people / institutions / projects that authored or curated tablet
data. The full search machinery (hybrid lexical+semantic) lives in /search;
this module exists so the web layer can render a Browse-Scholars listing
without making search a precondition for navigation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db

router = APIRouter(prefix="/scholars", tags=["scholars"])


@router.get("")
def list_scholars(
    search: str = "",
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=24, ge=1, le=100),
    has_artifacts: bool = Query(default=False),
    conn=Depends(get_db),
):
    offset = (page - 1) * per_page
    params: list = []
    conditions: list[str] = []

    if search.strip():
        conditions.append(
            "(s.normalized_name ILIKE %s OR s.name ILIKE %s OR s.institution ILIKE %s)"
        )
        like = f"%{search.strip()}%"
        params.extend([like, like, like])

    if has_artifacts:
        # Restrict to scholars linked to at least one artifact via annotation_runs.
        # The artifacts table carries annotation_run_id which links to the scholar
        # who produced that annotation run.
        conditions.append(
            "EXISTS ("
            "  SELECT 1 FROM annotation_runs ar"
            "  JOIN artifacts a ON a.annotation_run_id = ar.id"
            "  WHERE ar.scholar_id = s.id"
            ")"
        )

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    # When actively filtering/searching, surface the most productive scholars
    # first (highest artifact count). Fall back to alphabetical when browsing
    # without a query so the list is predictable.
    order_by = (
        "artifact_count DESC NULLS LAST, s.normalized_name NULLS LAST, s.name"
        if (search.strip() or has_artifacts)
        else "s.normalized_name NULLS LAST, s.name"
    )

    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM scholars s {where}", tuple(params))
        total = int(cur.fetchone()["n"])

        cur.execute(
            f"""
            SELECT s.id, s.name, s.normalized_name, s.orcid, s.institution,
                   s.expertise_periods, s.expertise_languages, s.author_type,
                   COUNT(DISTINCT a.p_number) AS artifact_count
            FROM scholars s
            LEFT JOIN annotation_runs ar ON ar.scholar_id = s.id
            LEFT JOIN artifacts a ON a.annotation_run_id = ar.id
            {where}
            GROUP BY s.id, s.name, s.normalized_name, s.orcid, s.institution,
                     s.expertise_periods, s.expertise_languages, s.author_type
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
            """,
            (*params, per_page, offset),
        )
        rows = cur.fetchall()

    items = [dict(r) for r in rows]
    total_pages = (total + per_page - 1) // per_page
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/{scholar_id}")
def get_scholar(scholar_id: int, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, normalized_name, orcid, institution,
                   expertise_periods, expertise_languages, active_since, author_type
            FROM scholars
            WHERE id = %s
            """,
            (scholar_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Scholar not found")
    return dict(row)
