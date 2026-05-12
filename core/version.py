"""Version surface shared by api/ and app/.

The release tag is written by `ops/deploy/deploy.sh` into `version.txt` at the
release root. The schema version is the highest `version` value in the
`public._migrations` tracking table — read lazily so an unreachable DB doesn't
break the process startup.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_STARTED_AT = datetime.now(timezone.utc)


@lru_cache(maxsize=1)
def release_tag() -> str:
    """Release tag from version.txt, or 'dev' when running outside a release."""
    version_file = _PROJECT_ROOT / "version.txt"
    if version_file.exists():
        tag = version_file.read_text().strip()
        if tag:
            return tag
    return os.getenv("APP_VERSION", "dev")


def environment() -> str:
    """`production`, `staging`, or `local` — derived from APP_ENV / release tag prefix."""
    explicit = os.getenv("APP_ENV", "").strip().lower()
    if explicit in {"production", "staging", "local"}:
        return explicit
    tag = release_tag()
    if tag.startswith("prod-"):
        return "production"
    if tag.startswith("staging-"):
        return "staging"
    return "local"


def schema_version() -> Optional[str]:
    """Highest applied migration version, or None when DB is unreachable."""
    try:
        from core.database import get_connection

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT version FROM public._migrations ORDER BY version DESC LIMIT 1"
                )
                row = cur.fetchone()
                if row is None:
                    return None
                # `dict_row` returns dicts; tuple cursors return sequences. Handle both.
                if isinstance(row, dict):
                    return row.get("version")
                return row[0]
    except Exception:
        return None


def started_at_iso() -> str:
    return _STARTED_AT.isoformat()


def version_payload() -> dict:
    """Shape returned by GET /version on the API and exposed to the web app's footer."""
    return {
        "release": release_tag(),
        "environment": environment(),
        "schema_version": schema_version(),
        "started_at": started_at_iso(),
    }
