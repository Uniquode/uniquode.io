from dataclasses import replace

from wevra.auth.options import (
    DEFAULT_SESSION_COOKIE_NAME as WEVRA_DEFAULT_SESSION_COOKIE_NAME,
)
from wevra.auth.settings import (
    DATABASE_URL_ENV,
    AuthSettings,
    load_auth_settings_from_config,
    validate_auth_settings,
)
from wevra.config import AppConfigSource, ConfigService

from app.settings import Settings

APP_SESSION_COOKIE_NAME = "uniquode_session"
LOCAL_DEPLOYMENT_ENVIRONMENT = "local"


def load_app_auth_settings(settings: Settings) -> AuthSettings:
    auth_settings = (
        load_auth_settings_from_config(
            ConfigService([AppConfigSource(settings.app_config)]),
            app_config=settings.app_config,
            environ=_auth_settings_environ(settings),
        )
        if settings.app_config is not None
        else AuthSettings(database_url=settings.database_url)
    )
    return _normalise_app_auth_settings(settings, auth_settings)


def _auth_settings_environ(settings: Settings) -> dict[str, str]:
    if settings.database_url is None:
        return {}

    return {DATABASE_URL_ENV: settings.database_url}


def _normalise_app_auth_settings(
    settings: Settings,
    auth_settings: AuthSettings,
) -> AuthSettings:
    identity_options = auth_settings.identity_options
    if identity_options.session_cookie_name == WEVRA_DEFAULT_SESSION_COOKIE_NAME:
        identity_options = replace(
            identity_options,
            session_cookie_name=APP_SESSION_COOKIE_NAME,
        )
        object.__setattr__(
            identity_options,
            "token_secrets_configured",
            auth_settings.identity_options.token_secrets_configured,
        )
        auth_settings = replace(auth_settings, identity_options=identity_options)

    validate_app_auth_settings(settings, auth_settings)
    return auth_settings


def validate_app_auth_settings(
    settings: Settings,
    auth_settings: AuthSettings,
) -> None:
    validate_auth_settings(
        auth_settings,
        allow_local_secrets=_allow_local_auth_secrets(settings),
    )


def _allow_local_auth_secrets(settings: Settings) -> bool:
    return settings.deployment_environment == LOCAL_DEPLOYMENT_ENVIRONMENT
