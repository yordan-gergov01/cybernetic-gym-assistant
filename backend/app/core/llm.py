"""Shared OpenAI client.

One AsyncOpenAI instance for the whole app: it holds a connection pool, so creating
clients per module (or worse, per request) wastes sockets and slows every call.
"""
from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import settings

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
