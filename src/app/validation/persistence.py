from wevra.db.migrate import migration_script_root
from wevra.db.persistence import (
    is_memory_database_url,
    is_supported_database_url,
)
from wevra.db.surfaces import (
    DataCompositionError,
    migration_version_locations_from_modules,
    model_packages_from_modules,
)
from wevra.db.urls import parse_sqlite_database_url, redact_database_url
from wevra.tools.validation.core import (
    ValidationCheck,
    ValidationResult,
    read_text_for_validation,
    record_check,
)

from app.settings import (
    DEFAULT_DATABASE_FILE,
    DEFAULT_DATABASE_URL,
    SQLITE_MEMORY_DATABASE_URL,
    Settings,
)


def validate_persistence(settings: Settings) -> ValidationResult:
    errors: list[str] = []
    checks: list[ValidationCheck] = []
    default_database_url = DEFAULT_DATABASE_URL
    display_database_url = redact_database_url(settings.database_url)
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

    migrations_root = migration_script_root(settings.migrations_root)
    has_migrations_root = record_check(
        checks,
        errors,
        passed=migrations_root.is_dir(),
        description=f"Alembic migrations root exists: {migrations_root}",
        error=f"Missing Alembic migrations root: {migrations_root}",
    )
    if has_migrations_root:
        for required_file in ("env.py", "script.py.mako"):
            required_path = migrations_root.joinpath(required_file)
            record_check(
                checks,
                errors,
                passed=required_path.is_file(),
                description=f"Alembic migration file exists: {required_file}",
                error=f"Missing Alembic migration file: {required_path}",
            )

        try:
            model_packages = model_packages_from_modules(settings.modules)
            version_locations = migration_version_locations_from_modules(
                settings.modules
            )
        except DataCompositionError as exc:
            record_check(
                checks,
                errors,
                passed=False,
                description="module migration version locations load",
                error=f"Module migration version location discovery failed: {exc}",
            )
            model_packages = ()
            version_locations = ()

        record_check(
            checks,
            errors,
            passed=not model_packages or bool(version_locations),
            description=(
                "module migration version locations exist: "
                + ", ".join(str(path) for path in version_locations)
            ),
            error=(
                "At least one configured module migration version location is required."
            ),
        )

        if model_packages:
            revision_files = tuple(
                sorted(
                    path
                    for version_location in version_locations
                    for path in version_location.glob("*.py")
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
            if has_revision_files and "wevra.auth" in settings.modules:
                revision_contents = [
                    content
                    for path in revision_files
                    if (
                        content := read_text_for_validation(
                            path,
                            checks,
                            errors,
                            description=(
                                f"Alembic revision reads as UTF-8: {path.name}"
                            ),
                        )
                    )
                    is not None
                ]
                revision_content = "\n".join(revision_contents)
                for table_name in (
                    "identity_user",
                    "identity_provider",
                    "identity_external_identity_link",
                    "identity_access_token",
                ):
                    record_check(
                        checks,
                        errors,
                        passed=table_name in revision_content,
                        description=f"Alembic migration creates table: {table_name}",
                        error=f"Alembic migration must create table: {table_name}",
                    )
        else:
            record_check(
                checks,
                errors,
                passed=True,
                description=(
                    "Alembic migration revisions optional without model modules"
                ),
                error=(
                    "Alembic migration revisions are only required when "
                    "configured modules expose model metadata."
                ),
            )

    record_check(
        checks,
        errors,
        passed=has_alembic_config and has_migrations_root,
        description=(
            "development database initialisation command is available: "
            "uv run wevra-migrate init"
        ),
        error=(
            "Development database initialisation requires Alembic config and "
            "migrations."
        ),
    )

    return ValidationResult(
        name="persistence", errors=tuple(errors), checks=tuple(checks)
    )
