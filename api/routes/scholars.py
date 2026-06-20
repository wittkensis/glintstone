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


@router.get("/{scholar_id}/contributions")
def get_scholar_contributions(
    scholar_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=50),
    conn=Depends(get_db),
):
    """Artifacts this scholar contributed to, joined through annotation_runs.

    Each row is one artifact that carries an annotation_run produced by this
    scholar. The `method` / `source_type` of that run is the attribution signal
    rendered as a method chip on the detail page. Newest run first (the most
    recent work is the most relevant), then by p_number for stable ordering.

    Counts are reported as distinct artifacts (`total`) and distinct annotation
    runs (`run_count`) — matching the list page's `artifact_count` semantics.
    Pagination is capped at 50 rows per page for v1; a prolific scholar's full
    ledger is a deliberate fast-follow.
    """
    offset = (page - 1) * per_page

    with conn.cursor() as cur:
        # Confirm the scholar exists so a bad id is a 404, not a silent empty list.
        cur.execute("SELECT 1 FROM scholars WHERE id = %s", (scholar_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Scholar not found")

        # Distinct artifacts attributed + distinct runs behind them. The list
        # page counts distinct p_number, so we mirror that here for consistency.
        cur.execute(
            """
            SELECT COUNT(DISTINCT a.p_number) AS total,
                   COUNT(DISTINCT ar.id)      AS run_count
            FROM annotation_runs ar
            JOIN artifacts a ON a.annotation_run_id = ar.id
            WHERE ar.scholar_id = %s
            """,
            (scholar_id,),
        )
        counts = cur.fetchone()
        total = int(counts["total"])
        run_count = int(counts["run_count"])

        cur.execute(
            """
            SELECT a.p_number, a.designation, a.object_type,
                   a.period_normalized, a.genre, a.language_normalized,
                   ar.method, ar.source_type, ar.created_at
            FROM annotation_runs ar
            JOIN artifacts a ON a.annotation_run_id = ar.id
            WHERE ar.scholar_id = %s
            ORDER BY ar.created_at DESC NULLS LAST, a.p_number
            LIMIT %s OFFSET %s
            """,
            (scholar_id, per_page, offset),
        )
        rows = cur.fetchall()

    items = [dict(r) for r in rows]
    total_pages = (total + per_page - 1) // per_page if total else 0
    return {
        "items": items,
        "total": total,
        "run_count": run_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/{scholar_id}/publications")
def get_scholar_publications(
    scholar_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=50),
    type: str = "",
    conn=Depends(get_db),
):
    """Publications authored/edited by this scholar, joined through
    publication_authors (the populated scholar↔publication junction).

    Each row is one publication this scholar is linked to, carrying their
    `role` (author/editor/translator/contributor) on that work. The default
    sort is most-cited first (``cited_by_count DESC NULLS LAST``) then newest
    year, so the reader sees impact before chronology — the Tufte data-ledger
    the detail page renders.

    Pagination is mandatory, not optional: the most prolific scholar in the
    corpus (#1595 "Unknown") carries 6,268 publications. We cap at 50 rows per
    page and report ``total`` / ``total_pages`` so the web layer can offer a
    "show all" affordance.

    Alongside the page of rows we return a one-shot **summary** (five aggregates
    for the stat strip) and a **type breakdown** (real per-type counts for the
    filter pills), so the detail page needs a single API round-trip. The
    optional ``type`` filter narrows the row list to one ``publication_type``;
    the summary and breakdown always describe the whole body of work so the
    pills keep their full counts while a filter is active.
    """
    offset = (page - 1) * per_page

    # Whitelist the type filter against the enum so a bad value is ignored
    # rather than silently returning nothing (and never reaches SQL untrusted).
    valid_types = {
        "monograph",
        "edited_volume",
        "journal_article",
        "series_volume",
        "digital_edition",
        "museum_catalog",
        "dissertation",
        "conference_paper",
        "hand_copy_publication",
        "chapter",
        "proceedings",
        "thesis",
        "report",
        "unpublished",
        "other",
    }
    type_filter = type.strip().lower() if type.strip().lower() in valid_types else ""

    with conn.cursor() as cur:
        # Confirm the scholar exists so a bad id is a 404, not a silent empty.
        cur.execute("SELECT 1 FROM scholars WHERE id = %s", (scholar_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Scholar not found")

        # Stat strip — five pre-computed aggregates over the whole body of work.
        cur.execute(
            """
            SELECT count(*)                              AS works,
                   coalesce(sum(p.cited_by_count), 0)    AS total_cites,
                   max(p.cited_by_count)                 AS top_cites,
                   min(p.year)                           AS first_year,
                   max(p.year)                           AS last_year,
                   count(DISTINCT p.publication_type)    AS type_count
            FROM publication_authors pa
            JOIN publications p ON p.id = pa.publication_id
            WHERE pa.scholar_id = %s
            """,
            (scholar_id,),
        )
        s = cur.fetchone()
        summary = {
            "works": int(s["works"]),
            "total_cites": int(s["total_cites"]),
            "top_cites": s["top_cites"],
            "first_year": s["first_year"],
            "last_year": s["last_year"],
            "type_count": int(s["type_count"]),
        }

        # Tablets edited — distinct artifacts edited via this scholar's pubs.
        cur.execute(
            """
            SELECT count(DISTINCT ae.p_number) AS tablets_edited
            FROM artifact_editions ae
            JOIN publication_authors pa ON pa.publication_id = ae.publication_id
            WHERE pa.scholar_id = %s
            """,
            (scholar_id,),
        )
        summary["tablets_edited"] = int(cur.fetchone()["tablets_edited"])

        # Type breakdown — real per-type counts for the filter pills.
        cur.execute(
            """
            SELECT p.publication_type AS type, count(*) AS n
            FROM publication_authors pa
            JOIN publications p ON p.id = pa.publication_id
            WHERE pa.scholar_id = %s
            GROUP BY p.publication_type
            ORDER BY n DESC
            """,
            (scholar_id,),
        )
        type_counts = [
            {"type": r["type"], "count": int(r["n"])} for r in cur.fetchall()
        ]

        # Paginated row list (optionally narrowed to one type).
        type_clause = "AND p.publication_type = %s" if type_filter else ""
        list_params: list = [scholar_id]
        if type_filter:
            list_params.append(type_filter)
        list_params.extend([per_page, offset])

        cur.execute(
            f"""
            SELECT p.id, p.title, p.short_title, p.publication_type, p.year,
                   p.publisher, p.doi, p.url, p.cited_by_count,
                   pa.role, pa.position
            FROM publication_authors pa
            JOIN publications p ON p.id = pa.publication_id
            WHERE pa.scholar_id = %s
              {type_clause}
            ORDER BY p.cited_by_count DESC NULLS LAST, p.year DESC NULLS LAST
            LIMIT %s OFFSET %s
            """,
            tuple(list_params),
        )
        rows = cur.fetchall()

    # `total` reflects the active filter so pagination is correct; the summary
    # and type breakdown stay whole-corpus (the pills keep their real counts).
    if type_filter:
        total = next((t["count"] for t in type_counts if t["type"] == type_filter), 0)
    else:
        total = summary["works"]

    items = [dict(r) for r in rows]
    total_pages = (total + per_page - 1) // per_page if total else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "summary": summary,
        "type_counts": type_counts,
        "type": type_filter,
    }
