"""Environment healthcheck: verifies everything the app needs is actually reachable.

Usage (from backend/):  python -m scripts.healthcheck

Checks config, database + migration revision, the FAISS vectorstore, the reranker
(if enabled) and R2 credentials. Exits non-zero if a required component is broken,
so it can gate a deploy.
"""
from __future__ import annotations

import asyncio
import sys

from app.core.config import settings

OK, WARN, FAIL = "OK  ", "WARN", "FAIL"


def _line(status: str, name: str, detail: str = "") -> None:
    print(f"[{status}] {name}{' — ' + detail if detail else ''}")


async def check_database() -> bool:
    try:
        from sqlalchemy import text

        from app.db.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
            rev = (await conn.execute(text("select version_num from alembic_version"))).scalar()
        _line(OK, "database", f"connected, migration revision {rev}")
        return True
    except Exception as e:
        _line(FAIL, "database", f"{type(e).__name__}: {str(e)[:120]}")
        return False


def check_vectorstore() -> bool:
    try:
        from app.components.retriever import load_index

        index, meta = load_index()
        _line(OK, "vectorstore", f"{index.ntotal} vectors, {len(meta)} chunks")
        return True
    except Exception as e:
        _line(FAIL, "vectorstore", f"{type(e).__name__}: {str(e)[:120]}")
        return False


def check_reranker() -> bool:
    if not settings.RERANK_ENABLED:
        _line(WARN, "reranker", "disabled (RERANK_ENABLED=false) — vector order only")
        return True
    from app.components.reranker import get_reranker

    if get_reranker() is None:
        _line(WARN, "reranker", f"{settings.RERANKER_MODEL} enabled but unavailable; falling back")
        return True
    _line(OK, "reranker", settings.RERANKER_MODEL)
    return True


def check_storage() -> bool:
    if not settings.r2_configured:
        _line(WARN, "R2 storage", "not configured — photo upload will return 503")
        return True
    try:
        from app.services import storage

        storage._client().head_bucket(Bucket=settings.R2_BUCKET)
        _line(OK, "R2 storage", f"bucket {settings.R2_BUCKET} reachable")
        return True
    except Exception as e:
        _line(FAIL, "R2 storage", f"{type(e).__name__}: {str(e)[:120]}")
        return False


def check_config() -> bool:
    missing = [k for k in ("OPENAI_API_KEY", "DATABASE_URL", "SECRET_KEY") if not getattr(settings, k, None)]
    if missing:
        _line(FAIL, "config", f"missing: {', '.join(missing)}")
        return False
    _line(OK, "config", f"env={settings.APP_ENV}, model={settings.PRIMARY_MODEL}")
    return True


async def main() -> int:
    print(f"--- {settings.APP_NAME} healthcheck ---")
    results = [check_config(), await check_database(), check_vectorstore(), check_reranker(), check_storage()]
    failed = results.count(False)
    print(f"--- {'all good' if not failed else f'{failed} check(s) FAILED'} ---")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
