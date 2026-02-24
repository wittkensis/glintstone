"""Artifact routes — search and detail."""

from fastapi import APIRouter, Depends, HTTPException, Query

from core.config import get_settings
from core.database import get_db
from api.repositories.artifact_repo import ArtifactRepository

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
    conn=Depends(get_db),
):
    repo = ArtifactRepository(conn)
    return repo.search(
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

    parsed = parse_atf_response(atf_data["lines"])
    raw_atf = build_raw_atf(atf_data["lines"])
    legend = get_legend_items(parsed["surfaces"])

    return {"atf": raw_atf, "parsed": parsed, "legend": legend}


@router.get("/{p_number}/translation")
def get_artifact_translation(p_number: str, conn=Depends(get_db)):
    """Get translation data for an artifact, grouped by language."""
    repo = ArtifactRepository(conn)
    return repo.get_translation(p_number)


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
    indexed = {}
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


@router.get("/{p_number}/sign-annotations")
def get_sign_annotations(p_number: str, conn=Depends(get_db)):
    """Get sign annotations (OCR bounding boxes) for overlay display."""
    repo = ArtifactRepository(conn)
    return repo.get_sign_annotations(p_number)


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
