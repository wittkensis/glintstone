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
    conn=Depends(get_db),
):
    offset = (page - 1) * per_page
    params: list = []
    where = ""
    if search.strip():
        where = (
            "WHERE normalized_name ILIKE %s OR name ILIKE %s OR institution ILIKE %s"
        )
        like = f"%{search.strip()}%"
        params.extend([like, like, like])

    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM scholars {where}", tuple(params))
        total = int(cur.fetchone()["n"])

        cur.execute(
            f"""
            SELECT id, name, normalized_name, orcid, institution,
                   expertise_periods, expertise_languages, author_type
            FROM scholars
            {where}
            ORDER BY normalized_name NULLS LAST, name
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
