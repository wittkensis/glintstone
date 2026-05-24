"""User routes — saved items (bookmarks), preferences."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Literal, Optional

from api.dependencies import require_user
from api.repositories.saved_items_repo import SavedItemsRepository
from api.repositories.user_repo import UserRepository
from core.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


VALID_THEMES = {"default", "lapis-clay", "scholars-studio", "instrument-panel"}


class SaveItemRequest(BaseModel):
    item_type: str
    item_id: str


class PreferencesRequest(BaseModel):
    theme: Literal["default", "lapis-clay", "scholars-studio", "instrument-panel"]


@router.patch("/me/preferences", status_code=204)
def update_preferences(
    body: PreferencesRequest,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    UserRepository(conn).update_theme(user["id"], body.theme)
    conn.commit()


@router.get("/me/saved-items")
def list_saved_items(
    item_type: Optional[str] = Query(default=None),
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    return SavedItemsRepository(conn).list_for_user(user["id"], item_type)


@router.post("/me/saved-items", status_code=201)
def save_item(
    body: SaveItemRequest,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    row = SavedItemsRepository(conn).save(user["id"], body.item_type, body.item_id)
    conn.commit()
    return row


@router.delete("/me/saved-items/{item_id}", status_code=204)
def delete_saved_item(
    item_id: str,
    user: dict = Depends(require_user),
    conn=Depends(get_db),
):
    deleted = SavedItemsRepository(conn).delete(item_id, user["id"])
    conn.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved item not found")
