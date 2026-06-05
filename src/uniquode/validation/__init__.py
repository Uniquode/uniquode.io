from tools.validation.core import ValidationCheck, ValidationResult
from uniquode.validation.environment import validate_environment
from uniquode.validation.persistence import validate_persistence

validation_targets = {
    "environment": validate_environment,
    "persistence": validate_persistence,
}

__all__ = (
    "ValidationCheck",
    "ValidationResult",
    "validate_environment",
    "validate_persistence",
    "validation_targets",
)
