"""The outbound HTTP client is shared, which is the whole point of it.

A client per call reopens a TCP connection and repeats the TLS handshake every time, and
the food lookup runs once per item in a meal. What these assert is the identity and the
lifecycle, not httpx itself.
"""
import pytest

from app.core.config import settings
from app.core.http import close_http_client, http_client


@pytest.fixture(autouse=True)
async def _closed_between_tests():
    """Each test starts and ends with no client, so none of them inherits another's."""
    await close_http_client()
    yield
    await close_http_client()


async def test_every_caller_gets_the_same_client():
    """Two calls returning two clients would mean two connection pools, which is the
    per-call handshake this module exists to remove."""
    assert http_client() is http_client()


async def test_the_client_carries_the_configured_timeout():
    """Without it a hanging third party holds the user's request open for as long as it
    likes; the timeout used to sit as a literal at the one call site."""
    client = http_client()

    assert client.timeout.read == settings.HTTP_TIMEOUT_SECONDS


async def test_closing_releases_the_pool():
    client = http_client()

    await close_http_client()

    assert client.is_closed


async def test_a_caller_after_shutdown_gets_a_working_client():
    """Anything that runs without the app's lifespan - a script, a test - must not fail
    on a client that was never opened or was already closed."""
    first = http_client()
    await close_http_client()

    second = http_client()

    assert second is not first
    assert not second.is_closed
