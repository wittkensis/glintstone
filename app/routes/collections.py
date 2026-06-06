"""Collection routes — CRUD and tablet management."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/collections")


@router.get("")
def collection_list(request: Request):
    api = request.app.state.api
    collections_page = api.list_collections()

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "collections/index.html",
        {
            "collections": collections_page.items,
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/new")
def collection_new(request: Request):
    from app.main import templates

    return templates.TemplateResponse(
        request,
        "collections/form.html",
        {"collection": None, "is_edit": False},
    )


@router.post("/new")
def collection_create(
    request: Request, name: str = Form(...), description: str = Form("")
):
    api = request.app.state.api
    result = api.post("/collections", json={"name": name, "description": description})
    return RedirectResponse(
        url=f"/collections/{result['collection_id']}", status_code=303
    )


@router.get("/{collection_id}")
def collection_detail(request: Request, collection_id: int, page: int = 1):
    api = request.app.state.api
    collection = api.get_collection(collection_id)
    if not collection:
        return RedirectResponse(url="/collections", status_code=302)

    # Tablets inside a collection use the passthrough — they're a sub-resource
    # not covered by a typed method yet, and they redirect explicitly on failure.
    try:
        tablets_data = api.get(
            f"/collections/{collection_id}/tablets",
            params={"page": page, "per_page": 24},
        )
    except Exception:
        tablets_data = {"items": [], "total": 0, "page": 1, "total_pages": 0}

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "collections/detail.html",
        {
            "collection": collection,
            "tablets": tablets_data.get("items", []),
            "total": tablets_data.get("total", 0),
            "page": tablets_data.get("page", 1),
            "total_pages": tablets_data.get("total_pages", 0),
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/{collection_id}/edit")
def collection_edit(request: Request, collection_id: int):
    api = request.app.state.api
    collection = api.get_collection(collection_id)
    if not collection:
        return RedirectResponse(url="/collections", status_code=302)

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "collections/form.html",
        {"collection": collection, "is_edit": True},
    )


@router.post("/{collection_id}/edit")
def collection_update(
    request: Request,
    collection_id: int,
    name: str = Form(...),
    description: str = Form(""),
):
    api = request.app.state.api
    api.put(
        f"/collections/{collection_id}", json={"name": name, "description": description}
    )
    return RedirectResponse(url=f"/collections/{collection_id}", status_code=303)


@router.post("/{collection_id}/delete")
def collection_delete(request: Request, collection_id: int):
    api = request.app.state.api
    api.delete(f"/collections/{collection_id}")
    return RedirectResponse(url="/collections", status_code=303)


@router.post("/{collection_id}/add-tablets")
def collection_add_tablets(
    request: Request, collection_id: int, p_numbers: str = Form(...)
):
    api = request.app.state.api
    pn_list = [p.strip() for p in p_numbers.split(",") if p.strip()]
    if pn_list:
        api.post(f"/collections/{collection_id}/tablets", json={"p_numbers": pn_list})
    return RedirectResponse(url=f"/collections/{collection_id}", status_code=303)


@router.post("/{collection_id}/remove-tablet")
def collection_remove_tablet(
    request: Request, collection_id: int, p_number: str = Form(...)
):
    api = request.app.state.api
    api.delete(f"/collections/{collection_id}/tablets/{p_number}")
    return RedirectResponse(url=f"/collections/{collection_id}", status_code=303)
