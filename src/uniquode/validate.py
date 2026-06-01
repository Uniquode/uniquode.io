import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import click

from uniquode.configuration import ConfigurationError
from uniquode.settings import Settings, load_settings
from uniquode.validation import (
    ValidationResult,
    get_validation_target,
    redact_secret_value,
    validate_environment,
    validate_persistence,
    validate_web,
    validation_target_names,
)
from uniquode.validation.web import _contains_post_form

VALIDATION_TARGETS = validation_target_names()

__all__ = (
    "UnknownValidationTargetError",
    "VALIDATION_TARGETS",
    "_contains_post_form",
    "main",
    "redact_secret_value",
    "validate_command",
    "validate_environment",
    "validate_persistence",
    "validate_web",
)


class UnknownValidationTargetError(ValueError):
    """Raised when validation is requested for unknown target names."""


@dataclass(frozen=True, slots=True)
class ValidationOverrides:
    database_url: str | None = None
    template_root: Path | None = None
    static_root: Path | None = None
    migrations_root: Path | None = None
    alembic_config: Path | None = None
    static_url_path: str | None = None


def _resolve_targets(targets: Sequence[str]) -> tuple[str, ...]:
    if not targets:
        return VALIDATION_TARGETS

    invalid_targets = sorted(set(targets) - set(VALIDATION_TARGETS))
    if invalid_targets:
        invalid = ", ".join(invalid_targets)
        raise UnknownValidationTargetError(f"Unknown validation target(s): {invalid}")

    return tuple(dict.fromkeys(targets))


def _build_settings(overrides: ValidationOverrides) -> Settings:
    defaults = load_settings()
    return Settings(
        app_name=defaults.app_name,
        deployment_environment=defaults.deployment_environment,
        database_url=(
            overrides.database_url
            if overrides.database_url is not None
            else defaults.database_url
        ),
        template_root=(
            overrides.template_root
            if overrides.template_root is not None
            else defaults.template_root
        ),
        static_root=(
            overrides.static_root
            if overrides.static_root is not None
            else defaults.static_root
        ),
        migrations_root=(
            overrides.migrations_root
            if overrides.migrations_root is not None
            else defaults.migrations_root
        ),
        alembic_config=(
            overrides.alembic_config
            if overrides.alembic_config is not None
            else defaults.alembic_config
        ),
        static_url_path=(
            overrides.static_url_path
            if overrides.static_url_path is not None
            else defaults.static_url_path
        ),
        csrf_token_secret=defaults.csrf_token_secret,
        csrf_cookie_secure=defaults.csrf_cookie_secure,
        identity_options=defaults.identity_options,
    )


@click.command(
    name="validate",
    context_settings={"help_option_names": ["-h", "--help"]},
    help=(
        "Run project validation checks. Examples: validate, "
        "validate --verbose web persistence."
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show the concrete validation checks performed for each target.",
)
@click.option(
    "--template-root",
    type=click.Path(path_type=Path),
    help="Override the configured template root for web validation.",
)
@click.option(
    "--static-root",
    type=click.Path(path_type=Path),
    help="Override the configured static root for web validation.",
)
@click.option(
    "--static-url-path",
    help="Override the configured static URL prefix for web validation.",
)
@click.option(
    "--database-url",
    help=(
        "Override the configured SQLAlchemy async database URL. Verbose output "
        "redacts embedded credentials."
    ),
)
@click.option(
    "--migrations-root",
    type=click.Path(path_type=Path),
    help="Override the configured Alembic migrations root.",
)
@click.option(
    "--alembic-config",
    type=click.Path(path_type=Path),
    help="Override the configured Alembic config file.",
)
@click.argument("targets", nargs=-1)
def validate_command(
    targets: tuple[str, ...],
    verbose: bool,
    template_root: Path | None,
    static_root: Path | None,
    static_url_path: str | None,
    database_url: str | None,
    migrations_root: Path | None,
    alembic_config: Path | None,
) -> int:
    overrides = ValidationOverrides(
        database_url=database_url,
        template_root=template_root,
        static_root=static_root,
        migrations_root=migrations_root,
        alembic_config=alembic_config,
        static_url_path=static_url_path,
    )
    try:
        settings = _build_settings(overrides)
    except ConfigurationError as exc:
        print("configuration: failed", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    exit_code = 0

    try:
        resolved_targets = _resolve_targets(targets)
    except UnknownValidationTargetError as exc:
        raise click.UsageError(str(exc)) from exc

    for target in resolved_targets:
        result = get_validation_target(target)(settings)

        if result.is_ok:
            print(f"{result.name}: ok")
            if verbose:
                _print_verbose_checks(result)
            continue

        exit_code = 1
        print(f"{result.name}: failed", file=sys.stderr)
        if verbose:
            _print_verbose_checks(result, file=sys.stderr)
        for error in result.errors:
            print(f"- {error}", file=sys.stderr)

    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = validate_command.main(
            args=None if argv is None else list(argv),
            prog_name="validate",
            standalone_mode=False,
        )
    except click.exceptions.Exit as exc:
        return int(exc.exit_code or 0)
    except click.ClickException as exc:
        exc.show()
        return int(exc.exit_code or 1)
    return int(result or 0)


def _print_verbose_checks(
    result: ValidationResult, *, file: TextIO | None = None
) -> None:
    output = sys.stdout if file is None else file
    for check in result.checks:
        status = "ok" if check.passed else "failed"
        print(f"  - {status}: {check.description}", file=output)
