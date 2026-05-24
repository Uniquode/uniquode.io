from __future__ import annotations

import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from uniquode.database_urls import is_supported_database_url, resolve_database_url
from uniquode.models import Base
from uniquode.settings import DEFAULT_DATABASE_URL

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _project_root() -> Path:
    if config.config_file_name is not None:
        return Path(config.config_file_name).resolve().parent

    return Path.cwd()


def _default_database_url() -> str:
    return resolve_database_url(DEFAULT_DATABASE_URL, _project_root())


def _database_url() -> str:
    explicit_url = context.get_x_argument(as_dictionary=True).get("database_url")
    for configured_url in (explicit_url, config.get_main_option("sqlalchemy.url")):
        if configured_url and configured_url.strip():
            return _validated_database_url(configured_url.strip())

    return _validated_database_url(_default_database_url())


def _validated_database_url(database_url: str) -> str:
    if is_supported_database_url(database_url):
        return database_url

    raise RuntimeError(
        "Alembic database URL uses an unsupported driver. "
        "Use sqlite+aiosqlite:// or postgresql+asyncpg://."
    )


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _database_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
