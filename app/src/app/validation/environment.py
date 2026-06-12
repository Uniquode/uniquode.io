from envex import Env
from wevra.tools.validation.core import ValidationCheck, ValidationResult, record_check

from app.configuration import ConfigurationError
from app.environment import (
    load_environment,
)
from app.settings import Settings


def validate_environment(settings: Settings) -> ValidationResult:
    errors: list[str] = []
    checks: list[ValidationCheck] = []

    _record_environment_loader_check(settings, checks, errors)

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
