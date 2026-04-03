"""Async HTTP client for the NetBox REST API."""

from __future__ import annotations

from typing import Any

import httpx

from netbox_skill.exceptions import (
    NetBoxAuthError,
    NetBoxClientError,
    NetBoxNotFoundError,
    NetBoxServerError,
    NetBoxValidationError,
)


class NetBoxClient:
    """Async client wrapping the NetBox REST API."""

    def __init__(self, url: str, token: str, verify_ssl: bool = True):
        self._base_url = url.rstrip("/")
        self._token = token
        self._verify_ssl = verify_ssl
        self._http: httpx.AsyncClient | None = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=f"{self._base_url}/api/",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                verify=self._verify_ssl,
                timeout=30.0,
            )
        return self._http

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        try:
            body = response.json()
        except Exception:
            body = response.text
        status = response.status_code
        if status in (401, 403):
            raise NetBoxAuthError(status_code=status, body=body)
        if status == 404:
            raise NetBoxNotFoundError(status_code=status, body=body)
        if status == 400:
            raise NetBoxValidationError(status_code=status, body=body)
        if status >= 500:
            raise NetBoxServerError(status_code=status, body=body)
        raise NetBoxClientError(status_code=status, body=body)

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        http = await self._get_http()
        response = await http.get(endpoint, params=params)
        self._raise_for_status(response)
        return response.json()

    async def get_all(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> list[dict]:
        http = await self._get_http()
        all_params = dict(params or {})
        all_params.setdefault("limit", 100)
        response = await http.get(endpoint, params=all_params)
        self._raise_for_status(response)
        data = response.json()
        results = list(data.get("results", []))
        next_url = data.get("next")
        while next_url:
            response = await http.get(next_url)
            self._raise_for_status(response)
            data = response.json()
            results.extend(data.get("results", []))
            next_url = data.get("next")
        return results

    async def create(
        self, endpoint: str, data: dict | list[dict]
    ) -> dict | list[dict]:
        http = await self._get_http()
        response = await http.post(endpoint, json=data)
        self._raise_for_status(response)
        return response.json()

    async def update(
        self,
        endpoint: str,
        id: int,
        data: dict[str, Any],
        partial: bool = True,
    ) -> dict:
        http = await self._get_http()
        url = f"{endpoint.rstrip('/')}/{id}/"
        if partial:
            response = await http.patch(url, json=data)
        else:
            response = await http.put(url, json=data)
        self._raise_for_status(response)
        return response.json()

    async def delete(self, endpoint: str, id: int) -> None:
        http = await self._get_http()
        url = f"{endpoint.rstrip('/')}/{id}/"
        response = await http.delete(url)
        self._raise_for_status(response)

    async def status(self) -> dict:
        http = await self._get_http()
        response = await http.get("status/")
        self._raise_for_status(response)
        return response.json()

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
