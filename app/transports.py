"""Transport layer for GlintstoneAPI — HTTP production, in-memory for tests."""

from typing import Protocol, runtime_checkable

import httpx


@runtime_checkable
class Transport(Protocol):
    def get(
        self, path: str, params: dict | None = None, token: str | None = None
    ) -> dict | list: ...
    def post(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict: ...
    def put(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict: ...
    def patch(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict | None: ...
    def delete(self, path: str, token: str | None = None) -> dict | None: ...
    def close(self) -> None: ...


class HttpxTransport:
    """Production transport using httpx."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def _auth_headers(self, token: str | None) -> dict:
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _check(self, r: httpx.Response) -> httpx.Response:
        # Import here to avoid circular import (api_client imports Transport)
        from app.api_client import AuthRequiredError

        if r.status_code == 401:
            raise AuthRequiredError()
        r.raise_for_status()
        return r

    def get(
        self, path: str, params: dict | None = None, token: str | None = None
    ) -> dict | list:
        return self._check(
            self._client.get(path, params=params, headers=self._auth_headers(token))
        ).json()

    def post(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict:
        return self._check(
            self._client.post(path, json=json, headers=self._auth_headers(token))
        ).json()

    def put(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict:
        return self._check(
            self._client.put(path, json=json, headers=self._auth_headers(token))
        ).json()

    def patch(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict | None:
        r = self._check(
            self._client.patch(path, json=json, headers=self._auth_headers(token))
        )
        return None if r.status_code == 204 else r.json()

    def delete(self, path: str, token: str | None = None) -> dict | None:
        r = self._check(self._client.delete(path, headers=self._auth_headers(token)))
        return None if r.status_code == 204 else r.json()

    def close(self) -> None:
        self._client.close()


class InMemoryTransport:
    """Test transport — returns fixture data without HTTP.

    Fixtures are keyed by path string. Unregistered paths return {} / None
    instead of raising, so tests only need to register the paths they care about.
    """

    def __init__(self, fixtures: dict[str, object]) -> None:
        self._fixtures = fixtures

    def get(
        self, path: str, params: dict | None = None, token: str | None = None
    ) -> dict | list:
        return self._fixtures.get(path, {})  # type: ignore[return-value]

    def post(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict:
        return self._fixtures.get(path, {})  # type: ignore[return-value]

    def put(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict:
        return self._fixtures.get(path, {})  # type: ignore[return-value]

    def patch(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict | None:
        return self._fixtures.get(path)  # type: ignore[return-value]

    def delete(self, path: str, token: str | None = None) -> dict | None:
        return None

    def close(self) -> None:
        pass
