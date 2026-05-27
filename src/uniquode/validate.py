import argparse
import sys
from pathlib import Path
from typing import TextIO

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
    "VALIDATION_TARGETS",
    "_contains_post_form",
    "build_parser",
    "main",
    "redact_secret_value",
    "validate_environment",
    "validate_persistence",
    "validate_web",
)


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


def _build_settings(args: argparse.Namespace) -> Settings:
    defaults = load_settings()
    return Settings(
        app_name=defaults.app_name,
        deployment_environment=defaults.deployment_environment,
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
        csrf_token_secret=defaults.csrf_token_secret,
        csrf_cookie_secure=defaults.csrf_cookie_secure,
        identity_options=defaults.identity_options,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = _build_settings(args)
    except ConfigurationError as exc:
        print("configuration: failed", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    exit_code = 0

    for target in _resolve_targets(args.targets):
        result = get_validation_target(target)(settings)

        if result.is_ok:
            print(f"{result.name}: ok")
            if args.verbose:
                _print_verbose_checks(result)
            continue

        exit_code = 1
        print(f"{result.name}: failed", file=sys.stderr)
        if args.verbose:
            _print_verbose_checks(result, file=sys.stderr)
        for error in result.errors:
            print(f"- {error}", file=sys.stderr)

    return exit_code


def _print_verbose_checks(
    result: ValidationResult, *, file: TextIO | None = None
) -> None:
    output = sys.stdout if file is None else file
    for check in result.checks:
        status = "ok" if check.passed else "failed"
        print(f"  - {status}: {check.description}", file=output)
