from urllib.parse import SplitResult, urlsplit, urlunsplit

from uniquode.database_urls import parse_sqlite_database_url
from uniquode.persistence import (
    is_memory_database_url,
    is_supported_database_url,
)
from uniquode.settings import (
    DEFAULT_DATABASE_FILE,
    DEFAULT_DATABASE_URL,
    SQLITE_MEMORY_DATABASE_URL,
    Settings,
)
from uniquode.validation.core import (
    ValidationCheck,
    ValidationResult,
    read_text_for_validation,
    record_check,
)


def validate_persistence(settings: Settings) -> ValidationResult:
    errors: list[str] = []
    checks: list[ValidationCheck] = []
    default_database_url = DEFAULT_DATABASE_URL
    display_database_url = redact_secret_value(settings.database_url)
    default_sqlite_url = parse_sqlite_database_url(default_database_url)

    record_check(
        checks,
        errors,
        passed=default_sqlite_url is not None
        and default_sqlite_url.path.name == DEFAULT_DATABASE_FILE.name
        and not is_memory_database_url(default_database_url),
        description=(
            f"default database URL uses persistent SQLite file: {default_database_url}"
        ),
        error="Default database URL must point to a persistent SQLite file.",
    )

    has_database_url = record_check(
        checks,
        errors,
        passed=bool(settings.database_url.strip()),
        description=f"database URL is configured: {display_database_url}",
        error="Database URL must not be empty.",
    )
    if has_database_url:
        record_check(
            checks,
            errors,
            passed=is_supported_database_url(settings.database_url),
            description="database URL uses supported async SQLAlchemy driver",
            error=(
                "Database URL must use sqlite+aiosqlite:// or postgresql+asyncpg://."
            ),
        )

    has_alembic_config = record_check(
        checks,
        errors,
        passed=settings.alembic_config.is_file(),
        description=f"Alembic config exists: {settings.alembic_config}",
        error=f"Missing Alembic config: {settings.alembic_config}",
    )
    if has_alembic_config:
        config_content = read_text_for_validation(
            settings.alembic_config,
            checks,
            errors,
            description=f"Alembic config reads as UTF-8: {settings.alembic_config}",
        )
    else:
        config_content = None

    if config_content is not None:
        record_check(
            checks,
            errors,
            passed="script_location" in config_content,
            description="Alembic config defines script_location",
            error=(
                f"Alembic config does not define script_location: "
                f"{settings.alembic_config}"
            ),
        )
        record_check(
            checks,
            errors,
            passed=SQLITE_MEMORY_DATABASE_URL not in config_content,
            description="Alembic config does not force in-memory SQLite",
            error="Alembic config must not force in-memory SQLite.",
        )

    has_migrations_root = record_check(
        checks,
        errors,
        passed=settings.migrations_root.is_dir(),
        description=f"Alembic migrations root exists: {settings.migrations_root}",
        error=f"Missing Alembic migrations root: {settings.migrations_root}",
    )
    if has_migrations_root:
        for required_file in ("env.py", "script.py.mako"):
            required_path = settings.migrations_root / required_file
            record_check(
                checks,
                errors,
                passed=required_path.is_file(),
                description=f"Alembic migration file exists: {required_file}",
                error=f"Missing Alembic migration file: {required_path}",
            )

        versions_root = settings.migrations_root / "versions"
        record_check(
            checks,
            errors,
            passed=versions_root.is_dir(),
            description=f"Alembic versions directory exists: {versions_root}",
            error=f"Missing Alembic versions directory: {versions_root}",
        )
        if versions_root.is_dir():
            revision_files = tuple(
                sorted(
                    path
                    for path in versions_root.glob("*.py")
                    if path.name != "__init__.py"
                )
            )
            has_revision_files = record_check(
                checks,
                errors,
                passed=bool(revision_files),
                description="Alembic migration revision exists",
                error="At least one Alembic migration revision is required.",
            )
            if has_revision_files:
                revision_contents = [
                    content
                    for path in revision_files
                    if (
                        content := read_text_for_validation(
                            path,
                            checks,
                            errors,
                            description=f"Alembic revision reads as UTF-8: {path.name}",
                        )
                    )
                    is not None
                ]
                revision_content = "\n".join(revision_contents)
                for table_name in (
                    "identity_user",
                    "identity_oauth_account",
                    "identity_access_token",
                ):
                    record_check(
                        checks,
                        errors,
                        passed=table_name in revision_content,
                        description=f"Alembic migration creates table: {table_name}",
                        error=f"Alembic migration must create table: {table_name}",
                    )

    record_check(
        checks,
        errors,
        passed=has_alembic_config and has_migrations_root,
        description=(
            "development database initialisation command is available: "
            "uv run alembic upgrade head"
        ),
        error=(
            "Development database initialisation requires Alembic config and "
            "migrations."
        ),
    )

    return ValidationResult(
        name="persistence", errors=tuple(errors), checks=tuple(checks)
    )


def redact_secret_value(value: str) -> str:
    return _redact_database_url(value)


def _redact_database_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value

    if not parsed.scheme or (parsed.username is None and parsed.password is None):
        return value

    credentials = "***:***" if parsed.password is not None else "***"
    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"

    try:
        port = parsed.port
    except ValueError:
        port = None
    if port is not None:
        host = f"{host}:{port}"

    netloc = f"{credentials}@{host}"
    return urlunsplit(
        SplitResult(
            scheme=parsed.scheme,
            netloc=netloc,
            path=parsed.path,
            query=parsed.query,
            fragment=parsed.fragment,
        )
    )
