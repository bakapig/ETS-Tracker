from __future__ import annotations

import httpx

from app.http_headers import outbound_headers

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            headers=outbound_headers(),
            follow_redirects=True,
            timeout=httpx.Timeout(120.0, connect=10.0),
        )
    return _client


async def close_http_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
