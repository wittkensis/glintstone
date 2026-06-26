"""Scholar routes — minimal listing + detail (read-only).

Scholars are people / institutions / projects that authored or curated tablet
data. The full search machinery (hybrid lexical+semantic) lives in /search;
this module exists so the web layer can render a Browse-Scholars listing
without making search a precondition for navigation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from api.dependencies import require_user
from core.database import get_db

router = APIRouter(prefix="/scholars", tags=["scholars"])

BIO_MAX_LEN = 1500


def _scholar_filters(
    search: str,
    has_artifacts: bool,
    has_orcid: bool,
    institution: list[str],
) -> tuple[list[str], list]:
    """Build the shared WHERE conditions + params for the scholars index.

    Factored out so the list endpoint and the facet-counts endpoint (#194)
    apply *exactly* the same predicates — the filter rail's counts must agree
    with the rows the same filters return, or the page lies to the reader.
    """
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

    if has_orcid:
        # An ORCID is the durable, disambiguating identifier for a real
        # researcher; this filter narrows the 86k-row directory to the
        # identified scholars (the data-rich subset worth browsing).
        conditions.append("s.orcid IS NOT NULL AND s.orcid <> ''")

    if institution:
        placeholders = ", ".join(["%s"] * len(institution))
        conditions.append(f"s.institution IN ({placeholders})")
        params.extend(institution)

    return conditions, params


@router.get("")
def list_scholars(
    search: str = "",
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=24, ge=1, le=100),
    has_artifacts: bool = Query(default=False),
    has_orcid: bool = Query(default=False),
    institution: list[str] = Query(default=[]),
    sort: str = "",
    conn=Depends(get_db),
):
    offset = (page - 1) * per_page
    conditions, params = _scholar_filters(search, has_artifacts, has_orcid, institution)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Sort policy (#183): the honest default for browsing a directory of
    # contributors is *most productive first* — a reader arriving cold should
    # meet the people who shaped the most of the record, not whoever sorts
    # first alphabetically. ``sort=alpha`` restores the predictable A→Z order;
    # an active text search also falls back to relevance-by-productivity.
    if sort == "alpha":
        order_by = "s.normalized_name NULLS LAST, s.name"
    else:
        order_by = (
            "artifact_count DESC NULLS LAST, s.normalized_name NULLS LAST, s.name"
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


@router.get("/facets")
def get_scholar_facets(
    search: str = "",
    has_artifacts: bool = Query(default=False),
    has_orcid: bool = Query(default=False),
    institution: list[str] = Query(default=[]),
    top: int = Query(default=20, ge=1, le=100),
    conn=Depends(get_db),
):
    """Facet counts for the all-scholars index filter rail (#194, dep of #183).

    Returns the count behind each filter option so the rail can show how many
    scholars each choice would surface — the same Tufte data-ledger pattern the
    dictionary's gloss-browse facets use (#163). Two dimensions today:

      ``institution`` — ``[{value, label, count}]``, busiest first, capped at
                        ``top``. Institution is sparsely populated in the corpus
                        (most ORACC scholar records carry no affiliation), so an
                        empty list here is the honest signal "no affiliations on
                        record" — the web layer hides the facet rather than
                        rendering a dead control.
      ``has_orcid``   — ``{with, without}`` counts: how many of the currently
                        matched scholars carry an ORCID identifier vs not.
      ``total``       — scholars matching the *other* active filters (the
                        denominator the rail describes).

    Counts are cross-filtered the way gloss-browse facets are: each facet's
    counts are computed against the OTHER active filters but ignore the facet's
    OWN selection, so selecting one institution doesn't zero out its siblings.
    """
    # Base predicate = everything EXCEPT institution (so the institution facet
    # shows its siblings) — but DO honour has_orcid/has_artifacts/search.
    base_conditions, base_params = _scholar_filters(
        search, has_artifacts, has_orcid, institution=[]
    )

    # The has_orcid facet counts ignore the has_orcid selection itself (so both
    # "with" and "without" stay visible) but honour the other filters.
    orcid_conditions, orcid_params = _scholar_filters(
        search, has_artifacts, has_orcid=False, institution=institution
    )
    orcid_where = "WHERE " + " AND ".join(orcid_conditions) if orcid_conditions else ""

    with conn.cursor() as cur:
        # Institution facet — busiest affiliations first. Skips blank/null so a
        # dead control never renders; the count is distinct scholars.
        inst_where_parts = list(base_conditions)
        inst_where_parts.append("s.institution IS NOT NULL AND s.institution <> ''")
        inst_where = "WHERE " + " AND ".join(inst_where_parts)
        cur.execute(
            f"""
            SELECT s.institution AS value, COUNT(*) AS n
            FROM scholars s
            {inst_where}
            GROUP BY s.institution
            ORDER BY n DESC, s.institution
            LIMIT %s
            """,
            (*base_params, top),
        )
        institutions = [
            {"value": r["value"], "label": r["value"], "count": int(r["n"])}
            for r in cur.fetchall()
        ]

        # has_orcid facet — with vs without, against the other active filters.
        cur.execute(
            f"""
            SELECT
                COUNT(*) FILTER (
                    WHERE s.orcid IS NOT NULL AND s.orcid <> ''
                ) AS with_orcid,
                COUNT(*) FILTER (
                    WHERE s.orcid IS NULL OR s.orcid = ''
                ) AS without_orcid
            FROM scholars s
            {orcid_where}
            """,
            tuple(orcid_params),
        )
        orcid_row = cur.fetchone()

        # Denominator — scholars matching the *fully* active filter set.
        all_conditions, all_params = _scholar_filters(
            search, has_artifacts, has_orcid, institution
        )
        all_where = "WHERE " + " AND ".join(all_conditions) if all_conditions else ""
        cur.execute(
            f"SELECT COUNT(*) AS n FROM scholars s {all_where}", tuple(all_params)
        )
        total = int(cur.fetchone()["n"])

    return {
        "total": total,
        "institution": institutions,
        "has_orcid": {
            "with": int(orcid_row["with_orcid"]),
            "without": int(orcid_row["without_orcid"]),
        },
    }


@router.get("/{scholar_id}")
def get_scholar(scholar_id: int, conn=Depends(get_db)):
    """Public scholar read model (#17 extends it with the claim overlay).

    When a verified claim + bio override exist, the overlay wins per field via
    COALESCE(override, ingested) — so the claimant's edits show without ever
    mutating the ORACC-ingested ``scholars`` row. The ``claim`` block tells the
    page whether to render the "Claimed · verified" badge, the bio, and the
    "edited by this scholar" markers. A bio/avatar surfaces ONLY when an APPROVED
    claim exists; a pending claim shows nothing public (spec decision #4).
    ``bio_overridden`` etc. let the template mark exactly which fields the
    scholar edited.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.name, s.normalized_name, s.orcid, s.active_since,
                   s.author_type,
                   COALESCE(o.institution, s.institution)               AS institution,
                   COALESCE(o.expertise_periods, s.expertise_periods)   AS expertise_periods,
                   COALESCE(o.expertise_languages, s.expertise_languages) AS expertise_languages,
                   s.institution         AS ingested_institution,
                   s.expertise_periods   AS ingested_expertise_periods,
                   s.expertise_languages AS ingested_expertise_languages,
                   o.bio                 AS bio,
                   o.homepage_url        AS homepage_url,
                   (o.institution IS NOT NULL)         AS institution_overridden,
                   (o.expertise_periods IS NOT NULL)   AS expertise_periods_overridden,
                   (o.expertise_languages IS NOT NULL) AS expertise_languages_overridden,
                   c.id          AS claim_id,
                   c.status      AS claim_status,
                   c.verified_at AS claim_verified_at,
                   c.verification_method AS claim_method,
                   u.display_name AS claimant_display_name,
                   u.avatar_url   AS claimant_avatar_url
            FROM scholars s
            LEFT JOIN scholar_claims c
                   ON c.scholar_id = s.id AND c.status = 'approved'
            LEFT JOIN scholar_overrides o ON o.scholar_id = s.id
            LEFT JOIN users u ON u.id = c.user_id
            WHERE s.id = %s
            """,
            (scholar_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Scholar not found")

    r = dict(row)
    verified = r.get("claim_status") == "approved"
    # Public surfaces (bio/avatar/badge) appear ONLY for a verified claim.
    claim = {
        "claimed": verified,
        "verified": verified,
        "verified_at": r.pop("claim_verified_at", None) if verified else None,
        "method": r.pop("claim_method", None) if verified else None,
        "claimant_display_name": r.get("claimant_display_name") if verified else None,
    }
    bio = r.get("bio") if verified else None
    homepage_url = r.get("homepage_url") if verified else None
    avatar_url = r.get("claimant_avatar_url") if verified else None

    return {
        "id": r["id"],
        "name": r["name"],
        "normalized_name": r["normalized_name"],
        "orcid": r["orcid"],
        "active_since": r["active_since"],
        "author_type": r["author_type"],
        "institution": r["institution"],
        "expertise_periods": r["expertise_periods"],
        "expertise_languages": r["expertise_languages"],
        # Per-field override flags (only meaningful when verified) so the page can
        # mark "· edited by this scholar" exactly where the scholar changed a value.
        "institution_overridden": bool(r["institution_overridden"]) and verified,
        "expertise_periods_overridden": bool(r["expertise_periods_overridden"])
        and verified,
        "expertise_languages_overridden": bool(r["expertise_languages_overridden"])
        and verified,
        "bio": bio,
        "homepage_url": homepage_url,
        "avatar_url": avatar_url,
        "claim": claim,
    }


class BioUpdateRequest(BaseModel):
    bio: str | None = None
    institution: str | None = None
    homepage_url: str | None = None
    expertise_periods: str | None = None
    expertise_languages: str | None = None


def _norm(value: str | None) -> str | None:
    """Empty/whitespace-only string → NULL so the field reverts to the ingested
    value via COALESCE rather than overriding it with a blank."""
    if value is None:
        return None
    v = value.strip()
    return v or None


@router.put("/{scholar_id}/bio")
def update_scholar_bio(
    scholar_id: int,
    body: BioUpdateRequest,
    request: Request,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    """Upsert the bio overlay for a scholar the caller has an APPROVED claim on.

    The load-bearing authorization check: the caller must hold the approved
    claim for this scholar_id, else 403 — a user cannot edit a profile they
    haven't claimed. Validates bio length and homepage URL shape. Blank fields
    clear the override (revert to the ingested value). Writes to
    ``scholar_overrides`` only; ``scholars`` is never mutated.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM scholar_claims "
            "WHERE scholar_id = %s AND user_id = %s AND status = 'approved'",
            (scholar_id, user["id"]),
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=403,
                detail="You can only edit a scholar profile you have claimed.",
            )

        bio = _norm(body.bio)
        if bio and len(bio) > BIO_MAX_LEN:
            raise HTTPException(
                status_code=400,
                detail=f"Biography must be {BIO_MAX_LEN} characters or fewer.",
            )
        homepage = _norm(body.homepage_url)
        if homepage and not (
            homepage.startswith("http://") or homepage.startswith("https://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Homepage must start with http:// or https://",
            )

        cur.execute(
            """
            INSERT INTO scholar_overrides
                (scholar_id, edited_by_user_id, bio, institution, homepage_url,
                 expertise_periods, expertise_languages, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (scholar_id) DO UPDATE SET
                edited_by_user_id   = EXCLUDED.edited_by_user_id,
                bio                 = EXCLUDED.bio,
                institution         = EXCLUDED.institution,
                homepage_url        = EXCLUDED.homepage_url,
                expertise_periods   = EXCLUDED.expertise_periods,
                expertise_languages = EXCLUDED.expertise_languages,
                updated_at          = now()
            RETURNING *
            """,
            (
                scholar_id,
                user["id"],
                bio,
                _norm(body.institution),
                homepage,
                _norm(body.expertise_periods),
                _norm(body.expertise_languages),
            ),
        )
        row = cur.fetchone()
    conn.commit()
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
        # pipeline_completeness join adds ATF/lemmatization coverage (#526).
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
                   MAX(ac.created_at)          AS created_at,
                   pc.has_atf,
                   pc.has_tokens,
                   pc.has_lemmatization,
                   ROUND((pc.lemma_ratio * 100)::numeric, 0)::int AS lemma_pct
            FROM artifact_contributors ac
            JOIN artifacts a ON a.p_number = ac.p_number
            LEFT JOIN pipeline_completeness pc ON pc.p_number = a.p_number
            WHERE ac.scholar_id = %s
            GROUP BY a.p_number, a.designation, a.object_type,
                     a.period_normalized, a.genre, a.language_normalized,
                     pc.has_atf, pc.has_tokens, pc.has_lemmatization, pc.lemma_ratio
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


CORRECTION_MAX_LEN = 500
_VALID_TARGET_TYPES = ("summary", "interpretation")
_VALID_REASONS = ("wrong_lemma", "wrong_translation", "missing_context", "other")


class CorrectionRequest(BaseModel):
    target_type: str  # 'summary' | 'interpretation'
    target_id: str  # p_number (summary) | token id (interpretation)
    correction_text: str
    reason: str  # wrong_lemma | wrong_translation | missing_context | other
    citation: str | None = None
    annotation_run_id: int | None = None


@router.post("/corrections", status_code=201)
def submit_correction(
    body: CorrectionRequest,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    """File a Level 2 scholar correction against a summary or interpretation (#532).

    The load-bearing authorization check: the caller must hold at least one
    APPROVED scholar_claims row, else 403 — only verified scholars may correct
    the corpus's machine output. We attribute the correction to the scholar_id
    of that approved claim (attribution is structural; never an anonymous edit).

    Validation: target_type and reason are closed enums; correction_text is
    required and capped at 500 chars (the DB enforces the same cap, but we 400
    here so the user sees a clean message instead of a constraint error).

    The INSERT uses no try/except UniqueViolation (rollback trap) — there is no
    uniqueness constraint to violate; a scholar may file multiple corrections.
    Status starts 'pending'; an admin reviews it later.
    """
    target_type = body.target_type.strip().lower()
    if target_type not in _VALID_TARGET_TYPES:
        raise HTTPException(
            status_code=400,
            detail="target_type must be 'summary' or 'interpretation'.",
        )
    reason = body.reason.strip().lower()
    if reason not in _VALID_REASONS:
        raise HTTPException(status_code=400, detail="Invalid reason.")
    text = (body.correction_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="A correction is required.")
    if len(text) > CORRECTION_MAX_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"A correction must be {CORRECTION_MAX_LEN} characters or fewer.",
        )
    target_id = (body.target_id or "").strip()
    if not target_id:
        raise HTTPException(status_code=400, detail="A target is required.")
    citation = (body.citation or "").strip() or None

    with conn.cursor() as cur:
        # Gate: caller must hold an approved claim. We take the scholar_id of that
        # claim as the correction's author (a user may have several approved
        # claims for ORACC-duplicate records; the most recent wins — any is a
        # valid verified identity for this user).
        cur.execute(
            "SELECT scholar_id FROM scholar_claims "
            "WHERE user_id = %s AND status = 'approved' "
            "ORDER BY verified_at DESC NULLS LAST LIMIT 1",
            (user["id"],),
        )
        claim = cur.fetchone()
        if not claim:
            raise HTTPException(
                status_code=403,
                detail="Only verified scholars can file corrections.",
            )

        cur.execute(
            """
            INSERT INTO scholar_corrections
                (scholar_id, target_type, target_id, correction_text, reason,
                 citation, status, annotation_run_id)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)
            RETURNING id, status, created_at
            """,
            (
                claim["scholar_id"],
                target_type,
                target_id,
                text,
                reason,
                citation,
                body.annotation_run_id,
            ),
        )
        row = cur.fetchone()
    conn.commit()
    return dict(row)


@router.get("/{scholar_id}/co-authors")
def get_scholar_co_authors(scholar_id: int, limit: int = Query(default=10, ge=1, le=50), conn=Depends(get_db)):
    """Scholars who frequently co-publish with this scholar (#525).

    Joins publication_authors twice to find scholars who share publications,
    returns the top N by shared publication count descending.
    Excludes the scholar themselves; 404 for unknown scholar_id.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM scholars WHERE id = %s", (scholar_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Scholar not found")

        cur.execute(
            """
            SELECT s.id, s.name, s.institution,
                   COUNT(DISTINCT pa1.publication_id) AS shared_count
            FROM publication_authors pa1
            JOIN publication_authors pa2
                ON pa2.publication_id = pa1.publication_id
               AND pa2.scholar_id != pa1.scholar_id
            JOIN scholars s ON s.id = pa2.scholar_id
            WHERE pa1.scholar_id = %s
            GROUP BY s.id, s.name, s.institution
            ORDER BY shared_count DESC, s.name
            LIMIT %s
            """,
            (scholar_id, limit),
        )
        rows = cur.fetchall()
    return {"items": [dict(r) for r in rows], "scholar_id": scholar_id}
