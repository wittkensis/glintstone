"""Artifact routes — search and detail."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from core.config import get_settings
from core.database import connect_one_shot, get_db
from core.storage import public_url_for_key
from api.repositories.artifact_repo import ArtifactRepository
from api.services.image_ondemand import ensure_images_for_artifact

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/filter-options")
def get_filter_options(
    period: list[str] = Query(default=[]),
    provenience: list[str] = Query(default=[]),
    genre: list[str] = Query(default=[]),
    language: list[str] = Query(default=[]),
    conn=Depends(get_db),
):
    repo = ArtifactRepository(conn)
    active = {
        "period": period,
        "provenience": provenience,
        "genre": genre,
        "language": language,
    }
    return repo.get_filter_options(active_filters=active)


@router.get("")
def search_artifacts(
    search: str | None = None,
    pipeline: str | None = None,
    period: list[str] = Query(default=[]),
    provenience: list[str] = Query(default=[]),
    genre: list[str] = Query(default=[]),
    language: list[str] = Query(default=[]),
    has_ocr: bool = False,
    page: int = 1,
    per_page: int = 24,
    include_filter_options: bool = False,
    conn=Depends(get_db),
):
    repo = ArtifactRepository(conn)
    result = repo.search(
        search=search,
        pipeline=pipeline,
        period=period or None,
        provenience=provenience or None,
        genre=genre or None,
        language=language or None,
        has_ocr=has_ocr,
        page=page,
        per_page=per_page,
    )
    # The repo LATERAL-joins a primary_thumbnail_key per row; turn it into a
    # browser-loadable thumbnail_url here so the web layer doesn't need to
    # know about R2 vs local-fs URL conventions.
    for item in result.get("items", []):
        key = item.pop("primary_thumbnail_key", None)
        item["thumbnail_url"] = public_url_for_key(key) if key else None

    # Optional one-trip filter options: the tablet list page needs both search
    # results and cross-filter counts. Letting the caller request both together
    # cuts a sequential httpx round trip out of the page render.
    if include_filter_options:
        result["filter_options"] = repo.get_filter_options(
            active_filters={
                "period": period,
                "provenience": provenience,
                "genre": genre,
                "language": language,
            }
        )

    return result


@router.get("/timeline")
def artifacts_timeline(
    search: str | None = None,
    pipeline: str | None = None,
    period: list[str] = Query(default=[]),
    provenience: list[str] = Query(default=[]),
    genre: list[str] = Query(default=[]),
    language: list[str] = Query(default=[]),
    has_ocr: bool = False,
    conn=Depends(get_db),
):
    """Per-period tablet counts over the current filter, for the Corpus-Atlas
    timeline view (#320). Returns {"items": [{canonical, date_start_bce,
    date_end_bce, group_name, count}, ...]} ordered chronologically.

    Accepts the same filter params as GET /artifacts so a brushed slice on the
    timeline reflects exactly the grid's active filters.
    """
    repo = ArtifactRepository(conn)
    items = repo.timeline_counts(
        search=search,
        pipeline=pipeline,
        period=period or None,
        provenience=provenience or None,
        genre=genre or None,
        language=language or None,
        has_ocr=has_ocr,
    )
    return {"items": items}


@router.get("/by-site")
def artifacts_by_site(
    search: str | None = None,
    pipeline: str | None = None,
    period: list[str] = Query(default=[]),
    provenience: list[str] = Query(default=[]),
    genre: list[str] = Query(default=[]),
    language: list[str] = Query(default=[]),
    has_ocr: bool = False,
    limit: int = 25,
    conn=Depends(get_db),
):
    """Ranked find-spots by tablet count over the current filter — the
    coordinate-free geography lens for the Corpus-Atlas (#320). Returns
    {"items": [{ancient_name, region, count}, ...]}, 'uncertain' excluded.
    """
    repo = ArtifactRepository(conn)
    items = repo.site_counts(
        search=search,
        pipeline=pipeline,
        period=period or None,
        provenience=provenience or None,
        genre=genre or None,
        language=language or None,
        has_ocr=has_ocr,
        limit=min(max(limit, 1), 100),
    )
    return {"items": items}


@router.get("/{p_number}")
def get_artifact(p_number: str, conn=Depends(get_db)):
    repo = ArtifactRepository(conn)
    artifact = repo.find_by_p_number(p_number)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.get("/{p_number}/atf")
def get_artifact_atf(p_number: str, conn=Depends(get_db)):
    """Get parsed ATF transliteration with surface grouping."""
    repo = ArtifactRepository(conn)
    atf_data = repo.get_atf(p_number)
    if not atf_data["lines"]:
        raise HTTPException(
            status_code=404, detail="No ATF data found for this artifact"
        )

    from api.services.atf_parser import (
        parse_atf_response,
        build_raw_atf,
        get_legend_items,
    )

    parsed = parse_atf_response(atf_data["lines"], atf_data.get("tokens_by_line"))
    raw_atf = build_raw_atf(atf_data["lines"])
    legend = get_legend_items(parsed["surfaces"])

    return {"atf": raw_atf, "parsed": parsed, "legend": legend}


@router.get("/{p_number}/translation")
def get_artifact_translation(p_number: str, conn=Depends(get_db)):
    """Get translation data for an artifact, grouped by language."""
    repo = ArtifactRepository(conn)
    return repo.get_translation(p_number)


@router.post("/{p_number}/images/ensure")
def ensure_artifact_images(
    p_number: str,
    background_tasks: BackgroundTasks,
    wait: bool = True,
    conn=Depends(get_db),
):
    """Idempotently fetch + cache CDLI images for an artifact.

    Two modes:
    - ``wait=true`` (default): block until the fetch completes (~5–15s),
      respond with the same shape as GET /images.
    - ``wait=false``: schedule the fetch in a BackgroundTasks queue and
      return ``{"status": "scheduled"}`` immediately. Use this when the UI
      will poll for the populated row separately.

    Safe to call concurrently: a per-artifact lock prevents duplicate fetches.
    Returns 'cached' immediately if rows already exist.
    """
    if wait:
        result = ensure_images_for_artifact(conn, p_number)
        return {
            "p_number": p_number,
            "status": result.status,
            "image_count": result.image_count,
            "detail": result.detail,
        }

    def _run_async() -> None:
        # BackgroundTasks runs after the response is sent; we open our own
        # short-lived connection rather than reusing the request-scoped one.
        bg_conn = connect_one_shot()
        try:
            ensure_images_for_artifact(bg_conn, p_number)
        finally:
            bg_conn.close()

    background_tasks.add_task(_run_async)
    return {"p_number": p_number, "status": "scheduled"}


@router.get("/{p_number}/images")
def get_artifact_images(p_number: str, conn=Depends(get_db)):
    """Image manifest for an artifact: R2 URLs + copyright per image.

    Returns rows from the artifact_images table (migration 022 / 023). The
    primary image is whichever row has the lowest display_order (typically a
    photograph at display_order=0). Each entry includes a thumbnail URL when
    available — UI cards should prefer the thumbnail. credit_line is
    display-ready and falls back to a 'pending verification' placeholder
    when attribution hasn't been backfilled yet.
    """
    repo = ArtifactRepository(conn)
    rows = repo.get_artifact_image_records(p_number)
    return {
        "p_number": p_number,
        "count": len(rows),
        "images": [
            {
                "id": r["id"],
                "image_type": r["image_type"],
                "cdli_reader_id": r["cdli_reader_id"],
                "original_url": public_url_for_key(r["r2_key"]),
                "thumbnail_url": (
                    public_url_for_key(r["r2_thumbnail_key"])
                    if r["r2_thumbnail_key"]
                    else None
                ),
                "mime_type": r["mime_type"],
                "byte_size": r["byte_size"],
                "width": r["width"],
                "height": r["height"],
                "copyright_holder": r["copyright_holder"],
                "license": r["license"],
                "attribution_raw": r["attribution_raw"],
                "credit_line": r["credit_line"],
                "display_order": r["display_order"],
                "ingested_at": r["ingested_at"].isoformat()
                if r.get("ingested_at")
                else None,
            }
            for r in rows
        ],
    }


@router.get("/{p_number}/surface-images")
def get_surface_images(p_number: str, conn=Depends(get_db)):
    """Per-surface image manifest for the tablet viewer (#129).

    Each entry is one physical surface image (obverse, reverse, …) with the
    ``surface_image_id`` the viewer passes to ``/image/{p}?surface_image_id=``
    and the stored pixel ``width``/``height`` used to scale that surface's
    sign-annotation overlays. ``surface`` is derived from the image path
    (``…/Obv`` → obverse, ``…/Rev`` → reverse) because the source
    ``surface_type`` column is unreliable. Dimensions may be ``null`` until the
    serving path backfills them on first view — the viewer then falls back to
    the loaded image's natural size for that surface.
    """
    repo = ArtifactRepository(conn)
    rows = repo.get_images(p_number)

    def _surface_label(row: dict) -> str:
        path = (row.get("image_path") or "").rstrip("/")
        tail = path.rsplit("/", 1)[-1].lower()
        if tail.startswith("obv"):
            return "obverse"
        if tail.startswith("rev"):
            return "reverse"
        return row.get("surface_type") or "surface"

    return {
        "p_number": p_number,
        "count": len(rows),
        "surfaces": [
            {
                "surface_image_id": r["surface_image_id"],
                "surface": _surface_label(r),
                "is_primary": bool(r.get("is_primary")),
                "image_type": r.get("image_type"),
                "width": r.get("image_width"),
                "height": r.get("image_height"),
            }
            for r in rows
        ],
    }


@router.get("/{p_number}/normalized")
def get_artifact_normalized(p_number: str, conn=Depends(get_db)):
    """Get normalized readings (scholarly transliteration) for an artifact."""
    repo = ArtifactRepository(conn)
    return repo.get_normalized(p_number)


@router.get("/{p_number}/lemmas")
def get_artifact_lemmas(p_number: str, conn=Depends(get_db)):
    """Get lemmatization data indexed by (line_no, word_no) for the viewer."""
    repo = ArtifactRepository(conn)
    result = repo.get_lemmas(p_number)

    # Index flat list into {lineNo: {wordNo: {...}}} for the ATF viewer.
    # line_number "1." → index 0, position 0 → key "0"
    indexed: dict = {}
    for row in result["lemmas"]:
        ln = row.get("line_number", "")
        # Parse "1." → 0, "2." → 1, "1'." → 0
        try:
            line_idx = int(str(ln).replace("'", "").rstrip(".")) - 1
        except (ValueError, TypeError):
            continue
        pos = row.get("position", 0)
        line_key = str(line_idx)
        word_key = str(pos)

        indexed.setdefault(line_key, {})[word_key] = {
            "gw": row.get("guide_word"),
            "cf": row.get("citation_form"),
            "pos": row.get("pos"),
            "epos": row.get("epos"),
            "lang": row.get("word_language") or row.get("token_lang"),
        }

    return {"p_number": result["p_number"], "lemmas": indexed, "total": result["total"]}


@router.get("/{p_number}/competing-lemmas")
def get_competing_lemmas(p_number: str, conn=Depends(get_db)):
    """Return tokens where multiple annotation runs disagree on the citation form.

    Response shape:
      {
        "p_number": "P123456",
        "competing": {
          "<line_idx>": {
            "<word_pos>": [
              {"citation_form": "...", "guide_word": "...", "confidence": 0.9,
               "source_type": "human", "source": "CDLI"},
              ...
            ]
          }
        }
      }

    Keys use the same (line_idx, word_pos) indexing as /lemmas so the ATF
    viewer can merge both datasets with a single lookup.
    """
    repo = ArtifactRepository(conn)
    return repo.get_competing_lemmas(p_number)


@router.get("/{p_number}/sign-annotations")
def get_sign_annotations(p_number: str, conn=Depends(get_db)):
    """Get sign annotations (OCR bounding boxes) for overlay display."""
    repo = ArtifactRepository(conn)
    return repo.get_sign_annotations(p_number)


@router.get("/{p_number}/sign-recognitions")
def get_sign_recognitions(p_number: str, conn=Depends(get_db)):
    """ML sign-reading predictions for a tablet (Akkademia, backlog #535).

    Returns the latest sign-recognition run's predictions in sign order, each
    with a derived confidence and the run's source attribution. Empty list when
    none exist.
    """
    repo = ArtifactRepository(conn)
    return repo.get_sign_recognitions(p_number)


@router.get("/{p_number}/research")
def get_artifact_research(p_number: str, conn=Depends(get_db)):
    """Return publications, scholars, and storage info for the Research tab."""
    repo = ArtifactRepository(conn)
    return repo.get_research(p_number)


@router.get("/citations/{doi:path}")
def get_citations(doi: str):
    """Fetch citing papers from Semantic Scholar for a DOI."""
    from api.services.semantic_scholar import get_citation_graph

    return get_citation_graph(doi)


@router.get("/{p_number}/debug")
def get_artifact_debug(p_number: str, conn=Depends(get_db)):
    """Return every data layer for a single artifact. Gated by DEBUG_TABLETS."""
    settings = get_settings()
    if not settings.app_debug:
        raise HTTPException(status_code=404, detail="Not found")
    repo = ArtifactRepository(conn)
    data = repo.debug_all(p_number)
    if not data:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return data
