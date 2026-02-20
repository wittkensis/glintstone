"""Collection routes — CRUD and tablet management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.database import get_db
from api.repositories.collection_repo import CollectionRepository

router = APIRouter(prefix="/collections", tags=["collections"])


class CollectionCreate(BaseModel):
    name: str
    description: str = ""


class CollectionUpdate(BaseModel):
    name: str
    description: str = ""


class TabletAdd(BaseModel):
    p_numbers: list[str]


@router.get("")
def list_collections(conn=Depends(get_db)):
    repo = CollectionRepository(conn)
    items = repo.get_all()
    return {"items": items}


@router.get("/random")
def random_collections(limit: int = 3, conn=Depends(get_db)):
    repo = CollectionRepository(conn)
    return repo.get_random(limit=limit)


@router.get("/{collection_id}")
def get_collection(collection_id: int, conn=Depends(get_db)):
    repo = CollectionRepository(conn)
    coll = repo.find_by_id(collection_id)
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    return coll


@router.get("/{collection_id}/tablets")
def get_collection_tablets(
    collection_id: int,
    page: int = 1,
    per_page: int = 24,
    conn=Depends(get_db),
):
    repo = CollectionRepository(conn)
    return repo.get_tablets(collection_id, page=page, per_page=per_page)


@router.post("")
def create_collection(body: CollectionCreate, conn=Depends(get_db)):
    repo = CollectionRepository(conn)
    result = repo.create(name=body.name, description=body.description)
    conn.commit()
    return result


@router.put("/{collection_id}")
def update_collection(collection_id: int, body: CollectionUpdate, conn=Depends(get_db)):
    repo = CollectionRepository(conn)
    result = repo.update(collection_id, name=body.name, description=body.description)
    if not result:
        raise HTTPException(status_code=404, detail="Collection not found")
    conn.commit()
    return result


@router.delete("/{collection_id}")
def delete_collection(collection_id: int, conn=Depends(get_db)):
    repo = CollectionRepository(conn)
    repo.delete(collection_id)
    return {"ok": True}


@router.post("/{collection_id}/tablets")
def add_tablets(collection_id: int, body: TabletAdd, conn=Depends(get_db)):
    repo = CollectionRepository(conn)
    added = repo.add_tablets(collection_id, body.p_numbers)
    return {"added": added}


@router.delete("/{collection_id}/tablets/{p_number}")
def remove_tablet(collection_id: int, p_number: str, conn=Depends(get_db)):
    repo = CollectionRepository(conn)
    repo.remove_tablet(collection_id, p_number)
    return {"ok": True}
