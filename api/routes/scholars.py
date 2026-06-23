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
        # Restrict to scholars credited on at least one artifact via the
        # artifact_contributors junction (#261). This mirrors the contributions
        # ledger so the filter and the detail page agree.
        conditions.append(
            "EXISTS ("
            "  SELECT 1 FROM artifact_contributors ac"
            "  WHERE ac.scholar_id = s.id"
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
                   COUNT(DISTINCT ac.p_number) AS artifact_count
            FROM scholars s
            LEFT JOIN artifact_contributors ac ON ac.scholar_id = s.id
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


@router.get("/{scholar_id}/activity")
def get_scholar_activity(scholar_id: int, conn=Depends(get_db)):
    """A compact activity profile for one scholar's contribution corpus (#157).

    What this is — and just as importantly, what it is *not*. The obvious read
    of "activity over time" is a calendar timeline (work per month/year). We
    deliberately do NOT build that here, because the only timestamp on a
    contribution link (``artifact_contributors.created_at``) is the backfill
    date — every credit this scholar holds shares one ingestion date, so a
    calendar chart would be a single misleading spike, not real history.

    The honest temporal signal is the **historical period of the tablets the
    scholar worked on**: a scholar of Neo-Assyrian letters and one of Ur III
    administrative texts have genuinely different activity profiles, and that
    spread is real data, not an ingestion artefact. So the timeline axis is the
    BCE timeline of the ancient texts, not a modern calendar — the same
    proportional-period histogram the lemma detail page uses (#201), reused
    verbatim on the client so the visual language stays consistent.

    Returns:
      ``periods``        — datable period bands for the #201 timeline, each
                           ``{period, date_start_bce, date_end_bce, tablet_count}``;
                           one bar = how many distinct tablets of that period the
                           scholar is credited on. Empty list when the scholar has
                           no datable contributions (page renders the #189 empty
                           state).
      ``dated_tablet_count``   — distinct tablets that fell into a datable period.
      ``undated_tablet_count`` — distinct contributed tablets with no datable
                           period (charted nowhere; surfaced as a footnote so the
                           page is honest about coverage).
      ``total_tablets``  — distinct tablets contributed (matches the ledger total).
      ``roles``          — ``[{role, count}]`` the scholar held, busiest first;
                           the second, non-temporal slice of "what they do".

    404 for a non-existent scholar id (never a silent empty profile).
    """
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM scholars WHERE id = %s", (scholar_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Scholar not found")

        # Per-period distinct-tablet counts for this scholar's credited
        # artifacts, joined to a de-duplicated period_canon for the BCE range.
        # DISTINCT ON (canonical) collapses period_canon's per-raw-spelling rows
        # to one canonical row, matching PeriodRepository.get_canonical_periods
        # and the lemma timeline so the axis is consistent app-wide.
        cur.execute(
            """
            WITH pc AS (
                SELECT DISTINCT ON (canonical)
                    canonical, date_start_bce, date_end_bce, sort_order
                FROM period_canon
                ORDER BY canonical, sort_order NULLS LAST
            ),
            tablets AS (
                SELECT DISTINCT ac.p_number, a.period_normalized
                FROM artifact_contributors ac
                JOIN artifacts a ON a.p_number = ac.p_number
                WHERE ac.scholar_id = %s
            )
            SELECT pc.canonical       AS period,
                   pc.date_start_bce,
                   pc.date_end_bce,
                   pc.sort_order,
                   COUNT(*)           AS tablet_count
            FROM tablets t
            JOIN pc ON pc.canonical = t.period_normalized
            WHERE pc.date_start_bce IS NOT NULL
              AND pc.date_end_bce   IS NOT NULL
            GROUP BY pc.canonical, pc.date_start_bce, pc.date_end_bce, pc.sort_order
            ORDER BY pc.sort_order NULLS LAST, pc.date_start_bce
            """,
            (scholar_id,),
        )
        period_rows = cur.fetchall()
        periods = [
            {
                "period": r["period"],
                "date_start_bce": r["date_start_bce"],
                "date_end_bce": r["date_end_bce"],
                "tablet_count": int(r["tablet_count"]),
            }
            for r in period_rows
        ]
        dated = sum(p["tablet_count"] for p in periods)

        # Total distinct contributed tablets (matches the ledger's `total`).
        cur.execute(
            "SELECT COUNT(DISTINCT p_number) AS n "
            "FROM artifact_contributors WHERE scholar_id = %s",
            (scholar_id,),
        )
        total_tablets = int(cur.fetchone()["n"])

        # Role breakdown — the non-temporal "what they do" slice, busiest first.
        cur.execute(
            """
            SELECT role, COUNT(DISTINCT p_number) AS n
            FROM artifact_contributors
            WHERE scholar_id = %s
            GROUP BY role
            ORDER BY n DESC, role
            """,
            (scholar_id,),
        )
        roles = [{"role": r["role"], "count": int(r["n"])} for r in cur.fetchall()]

    return {
        "scholar_id": scholar_id,
        "periods": periods,
        "dated_tablet_count": dated,
        "undated_tablet_count": max(total_tablets - dated, 0),
        "total_tablets": total_tablets,
        "roles": roles,
    }


@router.get("/{scholar_id}/contributions")
def get_scholar_contributions(
    scholar_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=50),
    conn=Depends(get_db),
):
    """Artifacts this scholar contributed to, via the artifact_contributors
    junction (#261 — real per-artifact attribution parsed from ORACC credits).

    Each row is one artifact this scholar is credited on, carrying the *role*
    they played (lemmatizer / editor / adapter / director / creator /
    contributor). Attribution is conservative: only exact, unambiguous matches
    against ``scholars.normalized_name`` are stored, so an empty ledger means
    "no high-confidence credit", never a silent mismatch.

    Response shape is unchanged from the previous annotation_runs-backed version
    so the #156/#177 detail template and pagination keep working. The role is
    surfaced in the ``method`` field (rendered as the method chip) and the
    source project in ``source_type``. ``created_at`` is null for backfilled
    credit links (the prose carries no per-link timestamp) — the template
    renders an em-dash for the date in that case.

    ``total`` is distinct artifacts (matching the list page's artifact_count
    semantics); ``run_count`` is the number of distinct roles this scholar held
    across the corpus (the detail page reads it as "across N annotation runs" —
    here it counts the distinct contribution roles, the analogous provenance
    unit). NB the ledger is ordered p_number ASC since backfilled links share no
    meaningful timestamp; newest-first returns once human runs add dated links.

    NOTE: annotation_runs.scholar_id is intentionally NOT read here. It is kept
    for its original purpose (future human annotation runs); it is all-NULL for
    the import-era corpus, which is exactly why this junction exists.
    """
    offset = (page - 1) * per_page

    with conn.cursor() as cur:
        # Confirm the scholar exists so a bad id is a 404, not a silent empty list.
        cur.execute("SELECT 1 FROM scholars WHERE id = %s", (scholar_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Scholar not found")

        # Distinct artifacts attributed + distinct roles behind them.
        cur.execute(
            """
            SELECT COUNT(DISTINCT ac.p_number) AS total,
                   COUNT(DISTINCT ac.role)     AS run_count
            FROM artifact_contributors ac
            WHERE ac.scholar_id = %s
            """,
            (scholar_id,),
        )
        counts = cur.fetchone()
        total = int(counts["total"])
        run_count = int(counts["run_count"])

        # One row per distinct artifact. An artifact may credit the scholar in
        # several roles; we collapse to one row and surface the highest-signal
        # role (lemmatizer > editor > adapter > director > creator > contributor)
        # so the method chip is deterministic. The aggregation also de-dupes a
        # scholar credited on the same artifact under multiple oracc_projects.
        cur.execute(
            """
            SELECT a.p_number, a.designation, a.object_type,
                   a.period_normalized, a.genre, a.language_normalized,
                   (ARRAY_AGG(ac.role ORDER BY
                        CASE ac.role
                            WHEN 'lemmatizer'  THEN 1
                            WHEN 'editor'      THEN 2
                            WHEN 'adapter'     THEN 3
                            WHEN 'director'    THEN 4
                            WHEN 'creator'     THEN 5
                            ELSE 6
                        END))[1]               AS method,
                   MIN(ac.oracc_project)       AS source_type,
                   MAX(ac.created_at)          AS created_at
            FROM artifact_contributors ac
            JOIN artifacts a ON a.p_number = ac.p_number
            WHERE ac.scholar_id = %s
            GROUP BY a.p_number, a.designation, a.object_type,
                     a.period_normalized, a.genre, a.language_normalized
            ORDER BY a.p_number
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
