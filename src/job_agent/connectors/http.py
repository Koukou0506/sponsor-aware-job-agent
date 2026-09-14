import asyncio
from typing import Any

import httpx


class ConnectorRateLimited(RuntimeError):
    """The public ATS endpoint rejected the request due to rate limiting."""


_RETRYABLE = (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError)


class ResilientHttpClient:
    def __init__(
        self,
        max_attempts: int = 3,
        min_wait_seconds: float = 0.25,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._max_attempts = max_attempts
        self._min_wait_seconds = min_wait_seconds
        self._transport = transport
        self._timeout_seconds = timeout_seconds

    async def get_json(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
    ) -> Any:
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            follow_redirects=True,
            transport=self._transport,
        ) as client:
            for attempt in range(1, self._max_attempts + 1):
                try:
                    response = await client.get(
                        url,
                        params=params,
                        headers={"Accept": "application/json"},
                    )
                    if response.status_code == 429:
                        raise ConnectorRateLimited(f"rate limited: {url}")
                    response.raise_for_status()
                    return response.json()
                except _RETRYABLE:
                    if attempt == self._max_attempts:
                        raise
                    await asyncio.sleep(self._min_wait_seconds * (2 ** (attempt - 1)))
        raise RuntimeError("unreachable")
