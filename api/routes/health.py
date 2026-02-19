"""GET /health — API and database status check."""

import sys
from datetime import datetime, timezone

from fastapi import APIRouter

from glintstone.config import get_settings
from glintstone.database import get_connection

router = APIRouter()


@router.get("/health")
def health_check():
    settings = get_settings()
    db_ok = False
    db_error = None

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                row = cur.fetchone()
                db_ok = row is not None and row.get("ok") == 1
    except Exception as e:
        db_error = str(e)

    response = {
        "status": "healthy" if db_ok else "degraded",
        "version": "2.0.0-dev",
        "database": "connected" if db_ok else "error",
        "python": sys.version.split()[0],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if db_error and settings.app_debug:
        response["db_error"] = db_error

    return response
