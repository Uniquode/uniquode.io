from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from uniquode.database_urls import (
    is_memory_database_url,
    is_supported_database_url,
    sqlite_database_path,
)
from uniquode.settings import Settings

__all__ = (
    "Database",
    "close_database",
    "create_database",
    "create_database_engine",
    "create_session_factory",
    "is_memory_database_url",
    "is_supported_database_url",
    "session_scope",
    "sqlite_database_path",
)


@dataclass(frozen=True, slots=True)
class Database:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]


def create_database_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url, pool_pre_ping=True)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def create_database(settings: Settings) -> Database:
    engine = create_database_engine(settings)
    return Database(engine=engine, session_factory=create_session_factory(engine))


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a bare async session.

    Callers own transaction semantics. Writes must either use helpers that
    commit internally or call ``commit``/``rollback`` explicitly.
    """
    async with session_factory() as session:
        yield session


async def close_database(database: Database | AsyncEngine) -> None:
    engine = database.engine if isinstance(database, Database) else database
    await engine.dispose()
