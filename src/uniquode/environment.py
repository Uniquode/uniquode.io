from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Final, cast

from envex import Env

from uniquode.configuration import ConfigurationError
from wevra.core.composition import APP_CONFIG_ENV
from wevra.core.settings import EnvironmentSetting

ENV_ACCOUNT_CREATION_POLICY: Final = "ACCOUNT_CREATION_POLICY"
ENV_ADVANCED_AUTH: Final = "ADVANCED_AUTH"
ENV_ALEMBIC_CONFIG: Final = "ALEMBIC_CONFIG"
ENV_APP_CONFIG: Final = APP_CONFIG_ENV
ENV_APP_ENV: Final = "APP_ENV"
ENV_APP_NAME: Final = "APP_NAME"
ENV_APP_RELOAD: Final = "APP_RELOAD"
ENV_CSRF_SECRET: Final = "CSRF_SECRET"
ENV_CSRF_SECURE: Final = "CSRF_SECURE"
ENV_DATABASE_URL: Final = "DATABASE_URL"
ENV_MIGRATIONS_ROOT: Final = "MIGRATIONS_ROOT"
ENV_OAUTH_LINKING: Final = "OAUTH_LINKING"
ENV_RESET_SECRET: Final = "RESET_SECRET"
ENV_SESSION_COOKIE: Final = "SESSION_COOKIE"
ENV_SESSION_FORCE_SECURE: Final = "SESSION_FORCE_SECURE"
ENV_SESSION_LIFETIME: Final = "SESSION_LIFETIME"
ENV_STATIC_ROOT: Final = "STATIC_ROOT"
ENV_STATIC_URL: Final = "STATIC_URL"
ENV_TEMPLATE_ROOT: Final = "TEMPLATE_ROOT"
ENV_VERIFICATION_SECRET: Final = "VERIFICATION_SECRET"

SETTINGS_ENV_SETTINGS: Final[tuple[EnvironmentSetting, ...]] = (
    EnvironmentSetting(ENV_ALEMBIC_CONFIG, "alembic_config", "path"),
    EnvironmentSetting(ENV_APP_ENV, "deployment_environment"),
    EnvironmentSetting(ENV_APP_NAME, "app_name"),
    EnvironmentSetting(ENV_CSRF_SECRET, "csrf_token_secret"),
    EnvironmentSetting(ENV_CSRF_SECURE, "csrf_cookie_secure", "bool"),
    EnvironmentSetting(ENV_DATABASE_URL, "database_url"),
    EnvironmentSetting(ENV_MIGRATIONS_ROOT, "migrations_root", "path"),
    EnvironmentSetting(ENV_STATIC_ROOT, "static_root", "path"),
    EnvironmentSetting(ENV_STATIC_URL, "static_url_path"),
    EnvironmentSetting(ENV_TEMPLATE_ROOT, "template_root", "path"),
)
IDENTITY_ENV_SETTINGS: Final[tuple[EnvironmentSetting, ...]] = (
    EnvironmentSetting(ENV_ACCOUNT_CREATION_POLICY, "account_creation_policy"),
    EnvironmentSetting(ENV_ADVANCED_AUTH, "advanced_authentication_enabled", "bool"),
    EnvironmentSetting(ENV_OAUTH_LINKING, "oauth_account_linking_enabled", "bool"),
    EnvironmentSetting(ENV_RESET_SECRET, "reset_password_token_secret"),
    EnvironmentSetting(ENV_SESSION_COOKIE, "session_cookie_name"),
    EnvironmentSetting(ENV_SESSION_FORCE_SECURE, "session_cookie_force_secure", "bool"),
    EnvironmentSetting(ENV_SESSION_LIFETIME, "session_lifetime_seconds", "int"),
    EnvironmentSetting(ENV_VERIFICATION_SECRET, "verification_token_secret"),
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
