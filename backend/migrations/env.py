"""Alembic migration environment.

The database URL is taken from application Settings (backend/.env) and the
target metadata from the SQLAlchemy models, so migrations always follow the
same source of truth as the running app. Migrations run synchronously via
psycopg2 even though the app itself uses asyncpg.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# `prepend_sys_path = .` in alembic.ini puts the backend root on the path.
from app.core.config import settings  # noqa: E402
from app.db.database import Base  # noqa: E402
import app.models  # noqa: E402,F401  (side effect: registers all tables on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _sync_db_url() -> str:
    """Force a synchronous (psycopg2) driver for Alembic regardless of app config."""
    url = settings.DATABASE_URL
    return url.replace("postgresql+asyncpg://", "postgresql://")


config.set_main_option("sqlalchemy.url", _sync_db_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
