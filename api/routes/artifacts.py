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
