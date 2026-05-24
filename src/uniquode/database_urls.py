from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

SQLITE_ASYNC_DATABASE_URL_PREFIX = "sqlite+aiosqlite:///"
SQLITE_MEMORY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
SUPPORTED_DATABASE_URL_PREFIXES = (
    "sqlite+aiosqlite://",
    "postgresql+asyncpg://",
)


@dataclass(frozen=True, slots=True)
class SqliteDatabaseUrl:
    path: Path
    query: str = ""
    fragment: str = ""

    @property
    def suffix(self) -> str:
        value = f"?{self.query}" if self.query else ""
        if self.fragment:
            value = f"{value}#{self.fragment}"

        return value


def is_supported_database_url(database_url: str) -> bool:
    return database_url.startswith(SUPPORTED_DATABASE_URL_PREFIXES)


def is_memory_database_url(database_url: str) -> bool:
    return database_url == SQLITE_MEMORY_DATABASE_URL


def parse_sqlite_database_url(database_url: str) -> SqliteDatabaseUrl | None:
    if is_memory_database_url(database_url):
        return None

    if not database_url.startswith(SQLITE_ASYNC_DATABASE_URL_PREFIX):
        return None

    parsed = urlsplit(database_url)
    if parsed.scheme != "sqlite+aiosqlite" or parsed.netloc or not parsed.path:
        return None

    path = parsed.path
    if path.startswith("//"):
        path = path[1:]
    else:
        path = path.removeprefix("/")

    return SqliteDatabaseUrl(
        path=Path(unquote(path)),
        query=parsed.query,
        fragment=parsed.fragment,
    )


def sqlite_database_path(database_url: str) -> Path | None:
    sqlite_url = parse_sqlite_database_url(database_url)
    return sqlite_url.path if sqlite_url is not None else None
