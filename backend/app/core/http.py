"""The shared HTTP client for outbound calls to third-party APIs.

A client per call means a fresh TCP connection and a fresh TLS handshake every time, and
the food lookup runs once per item in a meal - three foods logged together paid for three
handshakes to the same host. One client keeps a connection pool alive, so the second call
reuses the first one's connection.

The app opens it at startup and closes it at shutdown. `http_client()` also creates one
on demand, which is what keeps scripts and tests - anything that never runs the app's
lifespan - working instead of failing on a missing global.
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def http_client() -> httpx.AsyncClient:
    """The shared client, opened on first use if the app did not open it at startup."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
    return _client


async def close_http_client() -> None:
    """Release the pooled connections. Safe to call when nothing was ever opened."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        logger.info("Closed the shared HTTP client")
    _client = None
