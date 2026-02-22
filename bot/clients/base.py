from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ArrError(Exception):
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body}")


class BaseArrClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-Api-Key": api_key},
            timeout=30.0,
        )

    def _check(self, resp: httpx.Response) -> None:
        if resp.is_error:
            body = resp.text[:500]
            logger.error("API %s %s → %s: %s", resp.request.method, resp.request.url, resp.status_code, body)
            raise ArrError(resp.status_code, body)

    async def _get(self, path: str, **params: Any) -> Any:
        resp = await self._client.get(path, params=params)
        self._check(resp)
        return resp.json()

    async def _post(self, path: str, json: Any = None) -> Any:
        resp = await self._client.post(path, json=json)
        self._check(resp)
        return resp.json()

    async def _put(self, path: str, json: Any = None) -> Any:
        resp = await self._client.put(path, json=json)
        self._check(resp)
        return resp.json()

    async def _delete(self, path: str, **params: Any) -> None:
        resp = await self._client.delete(path, params=params)
        self._check(resp)

    async def close(self) -> None:
        await self._client.aclose()
