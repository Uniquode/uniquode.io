from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from importlib import import_module
from typing import Final

from sqlalchemy import MetaData

_MAX_AVAILABLE_ATTRIBUTE_NAMES: Final = 20
_METADATA_CACHE_SIZE: Final = 32

ENABLED_MODEL_PACKAGES: Final[tuple[str, ...]] = (
    "uniquode.models",
    "auth_ext.models",
)


def load_model_metadata(
    model_packages: Sequence[str] = ENABLED_MODEL_PACKAGES,
) -> tuple[MetaData, ...]:
    """Load SQLAlchemy metadata from an explicit model package list.

    Host applications can pass a different ordered package sequence to opt
    model packages in or out without changing the loader itself.
    """
    return tuple(
        _metadata_from_model_package(package_name) for package_name in model_packages
    )


@lru_cache(maxsize=_METADATA_CACHE_SIZE)
def _metadata_from_model_package(package_name: str) -> MetaData:
    try:
        module = import_module(package_name)
    except ModuleNotFoundError as exc:
        if _missing_configured_package(exc, package_name):
            raise RuntimeError(
                f"Model package {package_name!r} could not be imported."
            ) from None

        raise

    metadata = getattr(module, "metadata", None)
    if not isinstance(metadata, MetaData):
        raise RuntimeError(
            f"Model package {package_name!r} must expose SQLAlchemy metadata "
            "as a top-level `metadata` attribute. "
            f"Module origin: {_module_origin(module)}. "
            f"Available attributes: {_available_attribute_summary(module)}."
        )

    return metadata


def _missing_configured_package(exc: ModuleNotFoundError, package_name: str) -> bool:
    missing_name = exc.name
    return missing_name is not None and (
        missing_name == package_name or package_name.startswith(f"{missing_name}.")
    )


def _available_attribute_summary(module: object) -> str:
    names = sorted(name for name in dir(module) if not name.startswith("__"))
    if not names:
        return "<none>"

    visible_names = names[:_MAX_AVAILABLE_ATTRIBUTE_NAMES]
    summary = ", ".join(visible_names)
    hidden_count = len(names) - len(visible_names)
    if hidden_count > 0:
        return f"{summary}, ... (+{hidden_count} more)"

    return summary


def _module_origin(module: object) -> str:
    origin = getattr(module, "__file__", None)
    return origin if isinstance(origin, str) and origin else "<unknown>"
