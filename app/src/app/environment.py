from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Final, cast

from envex import Env
from wevra.auth.settings import IDENTITY_ENV_SETTINGS as wevra_identity_env_settings
from wevra.core.composition import APP_CONFIG_ENV
from wevra.core.settings import EnvironmentSetting

from app.config_definitions import (
    ENV_ALEMBIC_CONFIG,
    ENV_APP_ENV,
    ENV_APP_NAME,
    ENV_CSRF_SECRET,
    ENV_CSRF_SECURE,
    ENV_DATABASE_URL,
    ENV_MIGRATIONS_ROOT,
    ENV_STATIC_ROOT,
    ENV_STATIC_URL,
    ENV_TEMPLATE_ROOT,
    SETTINGS_ENV_SETTINGS,
)
from app.configuration import ConfigurationError

ENV_APP_CONFIG: Final = APP_CONFIG_ENV
ENV_APP_RELOAD: Final = "APP_RELOAD"

__all__ = (
    "ENV_ALEMBIC_CONFIG",
    "ENV_APP_CONFIG",
    "ENV_APP_ENV",
    "ENV_APP_NAME",
    "ENV_APP_RELOAD",
    "ENV_CSRF_SECRET",
    "ENV_CSRF_SECURE",
    "ENV_DATABASE_URL",
    "ENV_MIGRATIONS_ROOT",
    "ENV_STATIC_ROOT",
    "ENV_STATIC_URL",
    "ENV_TEMPLATE_ROOT",
    "IDENTITY_ENV_SETTINGS",
    "SETTINGS_ENV_SETTINGS",
    "SUPPORTED_ENV_VARS",
    "SUPPORTED_RUNSERVER_ENV_VARS",
    "SUPPORTED_SETTINGS_ENV_VARS",
    "load_environment",
)

IDENTITY_ENV_SETTINGS: Final[tuple[EnvironmentSetting, ...]] = (
    *wevra_identity_env_settings,
)
SUPPORTED_SETTINGS_ENV_VARS: Final = tuple(
    env_setting.name for env_setting in SETTINGS_ENV_SETTINGS + IDENTITY_ENV_SETTINGS
) + (ENV_APP_CONFIG,)

SUPPORTED_RUNSERVER_ENV_VARS: Final = (ENV_APP_RELOAD,)
SUPPORTED_ENV_VARS: Final = SUPPORTED_SETTINGS_ENV_VARS + SUPPORTED_RUNSERVER_ENV_VARS


def load_environment(
    *,
    environ: Mapping[str, str] | None = None,
    project_root: Path | None = None,
    read_dotenv: bool = True,
) -> Env:
    """Load process and local dotenv configuration through envex.

    When reading a local .env file, the returned Env instance is backed by a
    copy of the supplied environment so local dotenv loading does not mutate
    os.environ.
    """
    if environ is None:
        configured_environment: MutableMapping[str, str] = os.environ
    elif isinstance(environ, MutableMapping):
        configured_environment = cast(MutableMapping[str, str], environ)
    else:
        configured_environment = dict(environ)

    base_environment = (
        dict(configured_environment) if read_dotenv else configured_environment
    )
    try:
        return Env(
            environ=base_environment,
            readenv=read_dotenv,
            search_path=project_root or Path.cwd(),
            update=False,
        )
    except Exception as exc:
        # Treat envex/dotenv initialisation failures as configuration failures,
        # but do not expose raw exception text because it may contain secrets.
        raise ConfigurationError(
            "Environment loader failed while initialising envex "
            f"({type(exc).__name__})."
        ) from exc
