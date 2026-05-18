"""HTTP client for App → API communication."""

from typing import Optional

import httpx

from core.config import get_settings


class AuthRequiredError(Exception):
    """Raised when the API returns 401. The web app gate handles the redirect."""


class APIClient:
    """Server-side HTTP client for fetching data from the Glintstone API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.api_url
        self._client = httpx.Client(base_url=self.base_url, timeout=10.0)

    def _auth_headers(self, token: Optional[str]) -> dict:
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _check(self, r: httpx.Response) -> httpx.Response:
        if r.status_code == 401:
            raise AuthRequiredError()
        r.raise_for_status()
        return r

    def get(
        self,
        path: str,
        params: dict | None = None,
        token: Optional[str] = None,
    ) -> dict | list:
        r = self._check(
            self._client.get(path, params=params, headers=self._auth_headers(token))
        )
        return r.json()

    def post(
        self,
        path: str,
        json: dict | None = None,
        token: Optional[str] = None,
    ) -> dict:
        r = self._check(
            self._client.post(path, json=json, headers=self._auth_headers(token))
        )
        return r.json()

    def put(
        self,
        path: str,
        json: dict | None = None,
        token: Optional[str] = None,
    ) -> dict:
        r = self._check(
            self._client.put(path, json=json, headers=self._auth_headers(token))
        )
        return r.json()

    def delete(
        self,
        path: str,
        token: Optional[str] = None,
    ) -> dict | None:
        r = self._check(self._client.delete(path, headers=self._auth_headers(token)))
        if r.status_code == 204:
            return None
        return r.json()

    def close(self) -> None:
        self._client.close()
