import re
from typing import Final

from envex import Env

from uniquode.configuration import ConfigurationError
from uniquode.environment import (
    SUPPORTED_ENV_VARS,
    load_environment,
)
from uniquode.settings import Settings
from wevra.db.urls import redact_database_url
from wevra.tools.validation.core import ValidationCheck, ValidationResult, record_check

ENV_VAR_NAME_PATTERN: Final = re.compile(r"^[A-Z][A-Z0-9_]*$")


def validate_environment(settings: Settings) -> ValidationResult:
    errors: list[str] = []
    checks: list[ValidationCheck] = []

    for env_name in SUPPORTED_ENV_VARS:
        record_check(
            checks,
            errors,
            passed=bool(ENV_VAR_NAME_PATTERN.fullmatch(env_name)),
            description=f"supported environment variable name is valid: {env_name}",
            error=(
                "Supported environment variable names must use uppercase letters, "
                "digits, and underscores."
            ),
        )

    record_check(
        checks,
        errors,
        passed=len(SUPPORTED_ENV_VARS) == len(set(SUPPORTED_ENV_VARS)),
        description="supported environment variable names are unique",
        error="Supported environment variable names must be unique.",
    )

    _record_environment_loader_check(settings, checks, errors)

    record_check(
        checks,
        errors,
        passed=bool(settings.database_url.strip()),
        description=(
            "effective database URL is available: "
            f"{redact_database_url(settings.database_url)}"
        ),
        error="Effective database URL must not be empty.",
    )

    return ValidationResult(
        name="environment", errors=tuple(errors), checks=tuple(checks)
    )


def _record_environment_loader_check(
    settings: Settings,
    checks: list[ValidationCheck],
    errors: list[str],
) -> None:
    try:
        # This is an isolated wiring smoke check, not a read of the effective
        # process environment. `settings` already represents the configuration
        # being validated.
        loaded_env = load_environment(
            environ={},
            project_root=settings.project_root,
            read_dotenv=False,
        )
    except ConfigurationError as exc:
        record_check(
            checks,
            errors,
            passed=False,
            description="environment loader initialises envex with isolated input",
            error=str(exc),
        )
        return

    record_check(
        checks,
        errors,
        passed=isinstance(loaded_env, Env),
        description=(
            "environment loader returns an envex Env instance for isolated input"
        ),
        error=(
            "Environment loader returned "
            f"{type(loaded_env).__name__}; expected envex Env."
        ),
    )
