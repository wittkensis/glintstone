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


@router.get("/senses/{sense_id}")
def get_sense_detail(sense_id: int, conn=Depends(get_db)):
    """A single dictionary sense in full, with its lemma context (#184).

    Extends the dictionary's detail surface beyond the lemma: an addressable
    page for one meaning, carrying its definition / translations / source, the
    parent lemma, and the lemma's other senses (its polysemy). 404 for a
    non-existent sense id.
    """
    repo = LexicalRepository(conn)
    result = repo.get_sense_detail(sense_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sense not found")
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


@router.get("/lemmas/{lemma_id}/attestations")
def get_lemma_attestations(
    lemma_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
):
    """Tablet lines where this lemma is attested (#176).

    Each row is one text line where the lemma occurs, carrying its P-number,
    designation, line reference, transliterated ATF, and (where known) period /
    provenience / language. Paginated — a common lemma can occur on thousands
    of tablets. Returns ``items`` empty (not 404) for an existing lemma with no
    attestations so the page can render its empty state; 404 only for a
    non-existent lemma id.
    """
    repo = LexicalRepository(conn)
    result = repo.get_lemma_attestations(lemma_id, page=page, per_page=per_page)
    if result is None:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return result


@router.get("/lemmas/{lemma_id}/attestation-periods")
def get_lemma_attestation_periods(lemma_id: int, conn=Depends(get_db)):
    """Per-period attestation distribution for this lemma (#201).

    Groups the lemma's attesting tablets (same #176 join) by canonical
    historical period and returns a count per period alongside each period's
    BCE date range — the chronological spread of the word's usage, drawn as a
    proportional BCE timeline on the lemma detail page. ``periods`` is empty
    for an existing lemma with no datable attestations (the page renders the
    empty state); 404 only for a non-existent lemma id.
    """
    repo = LexicalRepository(conn)
    result = repo.get_lemma_attestation_periods(lemma_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return result


@router.get("/lemmas/{lemma_id}/norms")
def get_lemma_norms(lemma_id: int, conn=Depends(get_db)):
    """Get all normalized forms and their written spellings for a lemma."""
    repo = LexicalRepository(conn)
    norms = repo.get_norms_for_lemma(lemma_id)
    return {"lemma_id": lemma_id, "norms": norms}


@router.get("/lemmas/{lemma_id}/compositions")
def get_lemma_compositions(
    lemma_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    conn=Depends(get_db),
):
    """Compositions that contain this lemma (#529).

    Joins lemmatizations → tokens → text_lines → artifact_composites → composites
    to find compositions whose witness tablets carry this lemma. Returns the top N
    by attestation line count, so the most-represented compositions surface first.
    """
    repo = LexicalRepository(conn)
    lemma = repo.get_lemma_detail(lemma_id)
    if not lemma:
        raise HTTPException(status_code=404, detail="Lemma not found")
    citation_form = lemma.get("citation_form") or lemma.get("lemma", {}).get("citation_form")
    if not citation_form:
        return {"lemma_id": lemma_id, "items": []}

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.q_number, c.designation, c.language, c.period, c.genre,
                   COUNT(DISTINCT t.line_id) AS line_count
            FROM lemmatizations l
            JOIN tokens t ON t.id = l.token_id
            JOIN text_lines tl ON tl.id = t.line_id
            JOIN artifact_composites ac ON ac.p_number = tl.p_number
            JOIN composites c ON c.q_number = ac.q_number
            WHERE l.citation_form = %s
            GROUP BY c.q_number, c.designation, c.language, c.period, c.genre
            ORDER BY line_count DESC
            LIMIT %s
            """,
            (citation_form, limit),
        )
        rows = cur.fetchall()

    return {"lemma_id": lemma_id, "items": [dict(r) for r in rows]}


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
