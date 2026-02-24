"""Dictionary API routes — browse signs/lemmas/meanings, filter options, detail."""

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
    elif level == "meanings":
        return repo.browse_meanings(
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


@router.get("/meanings/{guide_word}")
def get_meaning_detail(
    guide_word: str,
    pos: str | None = None,
    conn=Depends(get_db),
):
    repo = LexicalRepository(conn)
    gw = unquote(guide_word)
    result = repo.get_meaning_detail(gw, pos)
    if not result:
        raise HTTPException(status_code=404, detail="Meaning group not found")
    return result
