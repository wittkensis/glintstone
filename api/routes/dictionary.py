"""Dictionary API routes — browse, search, detail."""

from fastapi import APIRouter, Depends, HTTPException, Query

from core.database import get_db
from api.repositories.glossary_repo import GlossaryRepository

router = APIRouter(prefix="/dictionary", tags=["dictionary"])


@router.get("/browse")
def browse_dictionary(
    search: str | None = None,
    group_type: str | None = None,
    group_value: str | None = None,
    sort: str = "frequency",
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    include_counts: bool = False,
    conn=Depends(get_db),
):
    """
    Browse dictionary entries with filtering and search.

    - **search**: Full-text search across headword, citation_form, guide_word
    - **group_type**: Filter category (pos, language, frequency)
    - **group_value**: Value within the group (e.g., "N" for noun, "akk" for Akkadian)
    - **sort**: Sort order (frequency DESC or alpha ASC)
    - **page**: Page number (1-indexed)
    - **per_page**: Items per page (1-200)
    - **include_counts**: Include grouping counts in response
    """
    repo = GlossaryRepository(conn)
    result = repo.browse(search, group_type, group_value, sort, page, per_page)

    if include_counts:
        result["counts"] = repo.get_grouping_counts()

    return result


@router.get("/counts")
def get_dictionary_counts(conn=Depends(get_db)):
    """
    Get counts for all filter categories.

    Returns counts grouped by:
    - all: Total entries
    - pos: Part of speech
    - language: Language family
    - frequency: Frequency buckets (1, 2-10, 11-100, 101-500, 500+)
    """
    repo = GlossaryRepository(conn)
    return repo.get_grouping_counts()


@router.get("/{entry_id:path}")
def get_dictionary_entry(entry_id: str, conn=Depends(get_db)):
    """
    Get full dictionary entry with variants, senses, and related words.

    Returns:
    - entry: Base fields (headword, citation_form, guide_word, pos, language, icount)
    - variants: Orthographic forms from glossary_forms
    - senses: Meanings from glossary_senses
    - related_words: Cross-references from glossary_relationships
    """
    repo = GlossaryRepository(conn)
    entry = repo.find_by_entry_id(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Add attestations (limited to 100)
    attestations = repo.get_attestations(entry_id, limit=100)
    entry["attestations"] = {
        "sample": attestations,
        "total_count": len(attestations),
        "showing": len(attestations),
    }

    return entry
