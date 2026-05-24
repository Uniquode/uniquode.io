from collections.abc import Callable, Mapping

from uniquode.settings import Settings
from uniquode.validation.core import ValidationResult
from uniquode.validation.persistence import validate_persistence
from uniquode.validation.web import validate_web

ValidationTarget = Callable[[Settings], ValidationResult]

VALIDATION_TARGETS: Mapping[str, ValidationTarget] = {
    "web": validate_web,
    "persistence": validate_persistence,
}


def validation_target_names() -> tuple[str, ...]:
    return tuple(VALIDATION_TARGETS)


def get_validation_target(name: str) -> ValidationTarget:
    return VALIDATION_TARGETS[name]
