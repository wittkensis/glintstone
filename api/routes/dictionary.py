"""Dictionary API routes — browse signs/lemmas/glosses, filter options, detail."""

from fastapi import APIRouter, Depends, HTTPException, Query
from urllib.parse import unquote

from core.database import get_db
from api.repositories.lexical_repo import LexicalRepository

router = APIRouter(prefix="/dictionary", tags=["dictionary"])


@router.get("/browse")
def browse_dictionary(
    level: str = "lemmas",
    search: str | None = None,
    language: list[str] = Query(default=[]),
    pos: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    frequency: str | None = None,
    sort: str = "frequency",
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    conn=Depends(get_db),
):
    repo = LexicalRepository(conn)

    if level == "signs":
        return repo.browse_signs(
            search=search,
            language=language or None,
            source=source or None,
            sort=sort,
            page=page,
            per_page=per_page,
        )
    elif level == "glosses":
        return repo.browse_glosses(
            search=search,
            language=language or None,
            pos=pos or None,
            sort=sort,
            page=page,
            per_page=per_page,
        )
    else:  # lemmas (default)
        return repo.browse_lemmas(
            search=search,
            language=language or None,
            pos=pos or None,
            source=source or None,
            frequency=frequency,
            sort=sort,
            page=page,
            per_page=per_page,
        )


@router.get("/filter-options")
def get_filter_options(
    level: str = "lemmas",
    language: list[str] = Query(default=[]),
    pos: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    frequency: str | None = None,
    conn=Depends(get_db),
):
    repo = LexicalRepository(conn)
    active: dict[str, list[str]] = {}
    if language:
        active["language"] = language
    if pos:
        active["pos"] = pos
    if source:
        active["source"] = source
    if frequency:
        active["frequency"] = [frequency]
    return repo.get_filter_options(level=level, active_filters=active)


@router.get("/signs/{sign_id}")
def get_sign_detail(sign_id: int, conn=Depends(get_db)):
    repo = LexicalRepository(conn)
    result = repo.get_sign_detail(sign_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sign not found")
    return result


@router.get("/lemmas/{lemma_id}")
def get_lemma_detail(lemma_id: int, conn=Depends(get_db)):
    repo = LexicalRepository(conn)
    result = repo.get_lemma_detail(lemma_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return result


@router.get("/lookup")
def lookup_written_form(
    form: str = Query(
        ..., min_length=1, description="Written/orthographic form to look up"
    ),
    language: str | None = Query(None, description="Language filter (e.g., akk, sux)"),
    conn=Depends(get_db),
):
    """Look up candidate lemmas for a written form via normalization bridge.

    Traverses: written_form -> normalized_form -> lemma -> glosses.
    Returns candidates ranked by attestation frequency.
    """
    repo = LexicalRepository(conn)
    return repo.lookup_by_written_form(form, language)


@router.get("/lemmas/{lemma_id}/norms")
def get_lemma_norms(lemma_id: int, conn=Depends(get_db)):
    """Get all normalized forms and their written spellings for a lemma."""
    repo = LexicalRepository(conn)
    norms = repo.get_norms_for_lemma(lemma_id)
    return {"lemma_id": lemma_id, "norms": norms}


@router.get("/glosses/{guide_word}")
def get_gloss_detail(
    guide_word: str,
    pos: str | None = None,
    conn=Depends(get_db),
):
    repo = LexicalRepository(conn)
    gw = unquote(guide_word)
    result = repo.get_gloss_detail(gw, pos)
    if not result:
        raise HTTPException(status_code=404, detail="Gloss group not found")
    return result
