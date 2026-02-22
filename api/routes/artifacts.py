"""Artifact routes — search and detail."""

from fastapi import APIRouter, Depends, HTTPException

from core.database import get_db
from api.repositories.artifact_repo import ArtifactRepository

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("")
def search_artifacts(
    search: str | None = None,
    pipeline: str | None = None,
    page: int = 1,
    per_page: int = 24,
    conn=Depends(get_db),
):
    repo = ArtifactRepository(conn)
    return repo.search(search=search, pipeline=pipeline, page=page, per_page=per_page)


@router.get("/{p_number}")
def get_artifact(p_number: str, conn=Depends(get_db)):
    repo = ArtifactRepository(conn)
    artifact = repo.find_by_p_number(p_number)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.get("/{p_number}/atf")
def get_artifact_atf(p_number: str, conn=Depends(get_db)):
    """Get ATF transliteration data for an artifact."""
    repo = ArtifactRepository(conn)
    atf_data = repo.get_atf(p_number)
    if not atf_data["lines"]:
        raise HTTPException(
            status_code=404, detail="No ATF data found for this artifact"
        )
    return atf_data


@router.get("/{p_number}/translation")
def get_artifact_translation(p_number: str, conn=Depends(get_db)):
    """Get translation data for an artifact."""
    repo = ArtifactRepository(conn)
    return repo.get_translation(p_number)


@router.get("/{p_number}/lemmas")
def get_artifact_lemmas(p_number: str, conn=Depends(get_db)):
    """Get lemmatization data for an artifact."""
    repo = ArtifactRepository(conn)
    return repo.get_lemmas(p_number)
