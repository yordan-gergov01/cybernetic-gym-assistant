"""A real database for the code that only SQL-compiles in the unit tests.

Everything under `tests/integration` runs against PostgreSQL, not SQLite: the models use
JSONB and UUID columns, and a stand-in that does not have them would prove nothing about
the queries this app actually runs.

The database named by `TEST_DATABASE_URL` is created if missing and every table in it is
dropped and rebuilt at the start of a session, so it must never be the app's own. Each
test runs inside a transaction that is rolled back afterwards - including the commits the
services make themselves, which land on a savepoint.

With no PostgreSQL server reachable the whole package skips with a reason instead of
failing: the pure-function suite still has to run on a machine without a database.
"""
from __future__ import annotations

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models  # noqa: F401  - registers every table on Base.metadata
from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app


def _test_db_url() -> str:
    url = settings.TEST_DATABASE_URL or f"{settings.DATABASE_URL}_test"
    return url.replace("postgresql://", "postgresql+asyncpg://")


async def _ensure_database(url: str) -> None:
    """Create the test database if it is not there yet."""
    server, _, name = url.replace("postgresql+asyncpg://", "postgresql://").rpartition("/")
    connection = await asyncpg.connect(f"{server}/postgres")
    try:
        exists = await connection.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", name)
        if not exists:
            await connection.execute(f'CREATE DATABASE "{name}"')
    finally:
        await connection.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    url = _test_db_url()
    try:
        await _ensure_database(url)
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"PostgreSQL is not reachable for the integration tests: {exc}")

    engine = create_async_engine(url, poolclass=None)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncSession:
    """A session whose work is undone when the test ends.

    The outer transaction is never committed; `join_transaction_mode="create_savepoint"`
    turns the commits inside the services into savepoint releases, so code under test can
    commit exactly as it does in production and still leave no rows behind.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = async_sessionmaker(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )()
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db) -> AsyncClient:
    """An HTTP client whose requests share the test's transaction."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
