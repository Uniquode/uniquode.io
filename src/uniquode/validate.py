import argparse
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import SplitResult, urlsplit, urlunsplit

from public.routes import build_public_route_set
from uniquode.database_urls import parse_sqlite_database_url
from uniquode.identity.routes import build_identity_route_set
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
from uniquode.web.renderer import TemplateRenderer
from uniquode.web.style_contract import (
    REQUIRED_STATIC_ASSETS,
    REQUIRED_THEME_SELECTORS,
    REQUIRED_THEME_TOKENS,
)

VALIDATION_TARGETS = ("web", "persistence")


class PostFormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.contains_post_form = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() != "form":
            return

        for name, value in attrs:
            if name.lower() == "method" and value is not None:
                if value.strip().lower() == "post":
                    self.contains_post_form = True
                return


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    description: str
    passed: bool


@dataclass(frozen=True, slots=True)
class ValidationResult:
    name: str
    errors: tuple[str, ...]
    checks: tuple[ValidationCheck, ...] = ()

    @property
    def is_ok(self) -> bool:
        return not self.errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate",
        description=(
            "Run project validation checks. Examples: validate, "
            "validate --verbose web persistence."
        ),
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Validation targets to run. Defaults to all registered targets.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show the concrete validation checks performed for each target.",
    )
    parser.add_argument(
        "--template-root",
        type=Path,
        help="Override the configured template root for web validation.",
    )
    parser.add_argument(
        "--static-root",
        type=Path,
        help="Override the configured static root for web validation.",
    )
    parser.add_argument(
        "--static-url-path",
        help="Override the configured static URL prefix for web validation.",
    )
    parser.add_argument(
        "--database-url",
        help=(
            "Override the configured SQLAlchemy async database URL. Verbose "
            "output redacts embedded credentials."
        ),
    )
    parser.add_argument(
        "--migrations-root",
        type=Path,
        help="Override the configured Alembic migrations root.",
    )
    parser.add_argument(
        "--alembic-config",
        type=Path,
        help="Override the configured Alembic config file.",
    )
    return parser


def _resolve_targets(targets: list[str]) -> tuple[str, ...]:
    if not targets:
        return VALIDATION_TARGETS

    invalid_targets = sorted(set(targets) - set(VALIDATION_TARGETS))
    if invalid_targets:
        invalid = ", ".join(invalid_targets)
        raise SystemExit(f"Unknown validation target(s): {invalid}")

    return tuple(dict.fromkeys(targets))


def _record_check(
    checks: list[ValidationCheck],
    errors: list[str],
    *,
    passed: bool,
    description: str,
    error: str | None = None,
) -> bool:
    checks.append(ValidationCheck(description=description, passed=passed))
    if not passed:
        errors.append(error or description)

    return passed


def _read_text_for_validation(
    path: Path,
    checks: list[ValidationCheck],
    errors: list[str],
    *,
    description: str,
) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _record_check(
            checks,
            errors,
            passed=False,
            description=description,
            error=f"Unable to read {path}: {exc}",
        )
        return None


def validate_web(settings: Settings) -> ValidationResult:
    errors: list[str] = []
    checks: list[ValidationCheck] = []

    _record_check(
        checks,
        errors,
        passed=settings.template_root.is_dir(),
        description=f"template root exists: {settings.template_root}",
        error=f"Missing template root: {settings.template_root}",
    )

    _record_check(
        checks,
        errors,
        passed=settings.static_root.is_dir(),
        description=f"static root exists: {settings.static_root}",
        error=f"Missing static root: {settings.static_root}",
    )

    _record_check(
        checks,
        errors,
        passed=bool(settings.static_url_path.strip()),
        description=f"static URL path is configured: {settings.static_url_path}",
        error="Static URL path must not be empty.",
    )

    route_sets = (build_public_route_set(), build_identity_route_set())
    renderer = TemplateRenderer(settings.template_root)

    for route_set in route_sets:
        route_definitions = tuple(route_set.page_routes) + tuple(
            getattr(route_set, "partial_routes", ())
        )
        for definition in route_definitions:
            template_name = getattr(definition.view, "template_name", None)
            if template_name is None:
                continue

            template_path = settings.template_root / template_name
            if not _record_check(
                checks,
                errors,
                passed=template_path.is_file(),
                description=(
                    f"route template exists: {definition.name} -> {template_name}"
                ),
                error=f"Missing template: {template_path}",
            ):
                continue

            template_content = _read_text_for_validation(
                template_path,
                checks,
                errors,
                description=f"template reads as UTF-8: {template_name}",
            )
            if template_content is None:
                continue

            if _contains_post_form(template_content):
                _record_check(
                    checks,
                    errors,
                    passed='name="{{ csrf_field_name }}"' in template_content,
                    description=f"POST form CSRF field exists: {template_name}",
                    error=(
                        f"POST form template must include CSRF field: {template_path}"
                    ),
                )

            try:
                renderer.environment.get_template(template_name)
            except Exception as exc:  # pragma: no cover - defensive guard
                _record_check(
                    checks,
                    errors,
                    passed=False,
                    description=f"template loads: {template_name}",
                    error=f"Template load failed for {template_name}: {exc}",
                )
            else:
                _record_check(
                    checks,
                    errors,
                    passed=True,
                    description=f"template loads: {template_name}",
                )

    for asset in REQUIRED_STATIC_ASSETS:
        asset_path = settings.static_root / asset
        if not _record_check(
            checks,
            errors,
            passed=asset_path.is_file(),
            description=f"static asset exists: {asset}",
            error=f"Missing static asset: {asset_path}",
        ):
            continue

        if asset != "styles/app.css":
            continue

        stylesheet_content = _read_text_for_validation(
            asset_path,
            checks,
            errors,
            description=f"static asset reads as UTF-8: {asset}",
        )
        if stylesheet_content is None:
            continue

        for token in REQUIRED_THEME_TOKENS:
            _record_check(
                checks,
                errors,
                passed=token in stylesheet_content,
                description=f"theme token present: {token}",
                error=f"Missing theme token: {token}",
            )

        for selector in REQUIRED_THEME_SELECTORS:
            _record_check(
                checks,
                errors,
                passed=selector in stylesheet_content,
                description=f"theme selector present: {selector}",
                error=f"Missing theme selector: {selector}",
            )

    return ValidationResult(name="web", errors=tuple(errors), checks=tuple(checks))


def _contains_post_form(template_content: str) -> bool:
    parser = PostFormParser()
    parser.feed(template_content)
    parser.close()
    return parser.contains_post_form


def validate_persistence(settings: Settings) -> ValidationResult:
    errors: list[str] = []
    checks: list[ValidationCheck] = []
    default_database_url = DEFAULT_DATABASE_URL
    display_database_url = redact_secret_value(settings.database_url)
    default_sqlite_url = parse_sqlite_database_url(default_database_url)

    _record_check(
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

    has_database_url = _record_check(
        checks,
        errors,
        passed=bool(settings.database_url.strip()),
        description=f"database URL is configured: {display_database_url}",
        error="Database URL must not be empty.",
    )
    if has_database_url:
        _record_check(
            checks,
            errors,
            passed=is_supported_database_url(settings.database_url),
            description="database URL uses supported async SQLAlchemy driver",
            error=(
                "Database URL must use sqlite+aiosqlite:// or postgresql+asyncpg://."
            ),
        )

    has_alembic_config = _record_check(
        checks,
        errors,
        passed=settings.alembic_config.is_file(),
        description=f"Alembic config exists: {settings.alembic_config}",
        error=f"Missing Alembic config: {settings.alembic_config}",
    )
    if has_alembic_config:
        config_content = _read_text_for_validation(
            settings.alembic_config,
            checks,
            errors,
            description=f"Alembic config reads as UTF-8: {settings.alembic_config}",
        )
    else:
        config_content = None

    if config_content is not None:
        _record_check(
            checks,
            errors,
            passed="script_location" in config_content,
            description="Alembic config defines script_location",
            error=(
                f"Alembic config does not define script_location: "
                f"{settings.alembic_config}"
            ),
        )
        _record_check(
            checks,
            errors,
            passed=SQLITE_MEMORY_DATABASE_URL not in config_content,
            description="Alembic config does not force in-memory SQLite",
            error="Alembic config must not force in-memory SQLite.",
        )

    has_migrations_root = _record_check(
        checks,
        errors,
        passed=settings.migrations_root.is_dir(),
        description=f"Alembic migrations root exists: {settings.migrations_root}",
        error=f"Missing Alembic migrations root: {settings.migrations_root}",
    )
    if has_migrations_root:
        for required_file in ("env.py", "script.py.mako"):
            required_path = settings.migrations_root / required_file
            _record_check(
                checks,
                errors,
                passed=required_path.is_file(),
                description=f"Alembic migration file exists: {required_file}",
                error=f"Missing Alembic migration file: {required_path}",
            )

        versions_root = settings.migrations_root / "versions"
        _record_check(
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
            has_revision_files = _record_check(
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
                        content := _read_text_for_validation(
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
                    _record_check(
                        checks,
                        errors,
                        passed=table_name in revision_content,
                        description=f"Alembic migration creates table: {table_name}",
                        error=f"Alembic migration must create table: {table_name}",
                    )

    _record_check(
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


def _build_settings(args: argparse.Namespace) -> Settings:
    defaults = Settings()
    return Settings(
        app_name=defaults.app_name,
        database_url=(
            args.database_url
            if args.database_url is not None
            else defaults.database_url
        ),
        template_root=(
            args.template_root
            if args.template_root is not None
            else defaults.template_root
        ),
        static_root=(
            args.static_root if args.static_root is not None else defaults.static_root
        ),
        migrations_root=(
            args.migrations_root
            if args.migrations_root is not None
            else defaults.migrations_root
        ),
        alembic_config=(
            args.alembic_config
            if args.alembic_config is not None
            else defaults.alembic_config
        ),
        static_url_path=(
            args.static_url_path
            if args.static_url_path is not None
            else defaults.static_url_path
        ),
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = _build_settings(args)
    exit_code = 0

    for target in _resolve_targets(args.targets):
        if target == "web":
            result = validate_web(settings)
        elif target == "persistence":
            result = validate_persistence(settings)

        if result.is_ok:
            print(f"{result.name}: ok")
            if args.verbose:
                _print_verbose_checks(result)
            continue

        exit_code = 1
        print(f"{result.name}: failed")
        if args.verbose:
            _print_verbose_checks(result)
        for error in result.errors:
            print(f"- {error}")

    return exit_code


def _print_verbose_checks(result: ValidationResult) -> None:
    for check in result.checks:
        status = "ok" if check.passed else "failed"
        print(f"  - {status}: {check.description}")
