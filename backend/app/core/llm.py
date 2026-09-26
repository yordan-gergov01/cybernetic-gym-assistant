"""Shared model clients.

One instance per provider for the whole app: each holds a connection pool, so creating
clients per module (or worse, per request) wastes sockets and slows every call.

Generation - chat, query rewriting, food extraction, program generation - goes to Groq
through its OpenAI-compatible API, which is why the OpenAI SDK is the client for it.
`openai_client` is left serving the query embeddings alone, until they move too.
"""
from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import settings

chat_client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url=settings.GROQ_BASE_URL,
    max_retries=settings.LLM_MAX_RETRIES,
)

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
