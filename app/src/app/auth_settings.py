from dataclasses import replace

from wevra.auth.options import (
    DEFAULT_SESSION_COOKIE_NAME as WEVRA_DEFAULT_SESSION_COOKIE_NAME,
)
from wevra.auth.options import is_generate_local_identity_secret
from wevra.auth.settings import (
    DATABASE_URL_ENV,
    AuthSettings,
    load_auth_settings_from_config,
)
from wevra.config import AppConfigSource, ConfigService

from app.configuration import ConfigurationError
from app.settings import Settings

APP_SESSION_COOKIE_NAME = "uniquode_session"


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
    if settings.deployment_environment == "local":
        return

    identity_options = auth_settings.identity_options
    if (
        is_generate_local_identity_secret(identity_options.reset_password_token_secret)
        or is_generate_local_identity_secret(identity_options.verification_token_secret)
        or not identity_options.token_secrets_configured
    ):
        raise ConfigurationError(
            "Non-local deployments must configure identity reset and "
            "verification token secrets."
        )
    if not identity_options.session_cookie_force_secure:
        raise ConfigurationError(
            "Non-local deployments must force secure session cookies; set "
            "SESSION_FORCE_SECURE=true or auth.session_cookie_force_secure = true."
        )
