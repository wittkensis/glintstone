"""Homepage route."""

from fastapi import APIRouter, Request

router = APIRouter()

# Editorial one-liners for the most-copied canonical texts.
# Keyed on lowercase designation prefix so partial matches work regardless of
# sub-title variations (e.g. "Gilgamesh Tablet XI" vs "Gilgamesh (XI)")
_CANON_DESCRIPTIONS: dict[str, str] = {
    "gilgamesh": "The Babylonian Flood narrative, copied for 2,000 years",
    "atrahasis": "The creation of humanity from clay mixed with divine blood",
    "enuma elish": "Marduk defeats Tiamat; the cosmos is organized from her body",
    "code of hammurabi": "282 laws governing Babylonian society, c. 1754 BCE",
    "lament for the destruction of ur": "A city goddess mourns as her city is destroyed",
    "descent of ishtar": "Ishtar descends to the underworld and returns — the dying-god cycle",
    "hymn to inanna": "Inanna exalted as queen of heaven and earth",
    "eduba": "Scribal school debates — how a student became a scribe",
    "lugalbanda": "The hero alone in the mountains, aided by a divine eagle",
    "angimdimma": "Ninurta's triumphant return from battle with captured monsters",
}


def _add_description(composite: dict) -> dict:
    desig = (composite.get("designation") or "").lower()
    for key, desc in _CANON_DESCRIPTIONS.items():
        if desig.startswith(key):
            return {**composite, "description": desc}
    return composite


@router.get("/")
def homepage(request: Request):
    api = request.app.state.api

    try:
        kpi = api.get("/stats/kpi")
    except Exception:
        kpi = None

    try:
        canon_data = api.get(
            "/composites", params={"limit": 7, "sort": "exemplar_count"}
        )
        canon = [_add_description(c) for c in canon_data.get("items", [])]
        composites_total = canon_data.get("total", 0)
    except Exception:
        canon = []
        composites_total = 0

    # Top browse facets for the Explore section
    top_periods = (kpi or {}).get("top_periods", [])[:5] if kpi else []
    top_genres = (kpi or {}).get("top_genres", [])[:5] if kpi else []
    top_languages = (kpi or {}).get("top_languages", [])[:5] if kpi else []

    # The Frontier: compositions with large unattested gaps (Phase 2)
    try:
        gaps_data = api.get("/stats/coverage-gaps", params={"limit": 4})
        frontier = gaps_data.get("items", [])
    except Exception:
        frontier = []

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "kpi": kpi,
            "canon": canon,
            "composites_total": composites_total,
            "frontier": frontier,
            "top_periods": top_periods,
            "top_genres": top_genres,
            "top_languages": top_languages,
            "api_url": request.app.state.api.base_url,
        },
    )
