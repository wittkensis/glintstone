"""HTTP client for App → API communication."""

import httpx

from core.config import get_settings


class APIClient:
    """Server-side HTTP client for fetching data from the Glintstone API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.api_url
        self._client = httpx.Client(base_url=self.base_url, timeout=10.0)

    def get(self, path: str, params: dict | None = None) -> dict | list:
        r = self._client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, json: dict | None = None) -> dict:
        r = self._client.post(path, json=json)
        r.raise_for_status()
        return r.json()

    def put(self, path: str, json: dict | None = None) -> dict:
        r = self._client.put(path, json=json)
        r.raise_for_status()
        return r.json()

    def delete(self, path: str) -> dict:
        r = self._client.delete(path)
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._client.close()
