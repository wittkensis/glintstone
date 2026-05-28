"""HTTP client that all MCP tools share. Calls the Glintstone REST API.

Keeps MCP and REST in lockstep — every tool is just an HTTP call to the same
service the web app uses. If the API contract changes, MCP gets it for free.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://api.glintstone.test"


class APIError(RuntimeError):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"API {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class GlintstoneAPIClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        client_label: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("GS_API_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.client_label = (
            client_label or os.environ.get("GS_CLIENT_LABEL") or "mcp-stdio"
        )
        headers = {
            "User-Agent": f"glintstone-mcp/{self.client_label}",
            "X-Glintstone-Client": self.client_label,
        }
        self._client = httpx.Client(
            base_url=self.base_url, timeout=timeout, headers=headers
        )

    def get(self, path: str, params: dict | None = None) -> dict:
        resp = self._client.get(path, params=params)
        if resp.status_code >= 400:
            raise APIError(resp.status_code, resp.text[:500])
        return resp.json()

    def post(self, path: str, body: dict) -> dict:
        resp = self._client.post(path, json=body)
        if resp.status_code >= 400:
            raise APIError(resp.status_code, resp.text[:500])
        return resp.json()

    def close(self) -> None:
        self._client.close()
