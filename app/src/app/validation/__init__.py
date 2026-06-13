from wevra.tools.validation.core import ValidationCheck, ValidationResult

from app.validation.environment import validate_environment

validation_targets = {
    "environment": validate_environment,
}

__all__ = (
    "ValidationCheck",
    "ValidationResult",
    "validate_environment",
    "validation_targets",
)
