import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from secrets import token_urlsafe
from typing import Any, Final, Literal, cast, get_args

from envex import Env

from auth_ext.options import (
    IdentityOptions,
    is_generate_local_identity_secret,
)
from uniquode.configuration import ConfigurationError
from uniquode.database_urls import (
    SQLITE_ASYNC_DATABASE_URL_PREFIX,
    SQLITE_MEMORY_DATABASE_URL,
    resolve_database_url,
)
from uniquode.environment import (
    IDENTITY_ENV_SETTINGS,
    SETTINGS_ENV_SETTINGS,
    EnvironmentSetting,
    load_environment,
)

__all__ = (
    "DEFAULT_ALEMBIC_CONFIG",
    "DEFAULT_DATABASE_FILE",
    "DEFAULT_DATABASE_URL",
    "DEFAULT_MIGRATIONS_ROOT",
    "DEFAULT_STATIC_ROOT",
    "DEFAULT_TEMPLATE_ROOT",
    "ALLOWED_DEPLOYMENT_ENVIRONMENTS",
    "ConfigurationError",
    "DEPLOYMENT_ENVIRONMENT_ERROR",
    "DeploymentEnvironment",
    "SQLITE_ASYNC_DATABASE_URL_PREFIX",
    "SQLITE_MEMORY_DATABASE_URL",
    "Settings",
    "load_settings",
)

DeploymentEnvironment = Literal["local", "staging", "production"]
ALLOWED_DEPLOYMENT_ENVIRONMENTS: Final[tuple[DeploymentEnvironment, ...]] = cast(
    tuple[DeploymentEnvironment, ...],
    get_args(DeploymentEnvironment),
)
DEPLOYMENT_ENVIRONMENT_ERROR: Final = (
    "Deployment environment must be one of: "
    + ", ".join(ALLOWED_DEPLOYMENT_ENVIRONMENTS)
    + "."
)

DEFAULT_TEMPLATE_ROOT = Path("src/templates")
DEFAULT_STATIC_ROOT = Path("src/static")
DEFAULT_MIGRATIONS_ROOT = Path("src/uniquode/migrations")
DEFAULT_ALEMBIC_CONFIG = Path("alembic.ini")
DEFAULT_DATABASE_FILE = Path("uniquode.sqlite3")
DEFAULT_DATABASE_URL = (
    f"{SQLITE_ASYNC_DATABASE_URL_PREFIX}{DEFAULT_DATABASE_FILE.as_posix()}"
)
CSRF_TOKEN_SECRET_BYTES = 32
_GENERATE_LOCAL_CSRF_SECRET = "__generate-local-csrf-secret__"

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "uniquode"
    deployment_environment: DeploymentEnvironment = "local"
    database_url: str = DEFAULT_DATABASE_URL
    project_root: Path = field(default_factory=Path.cwd)
    template_root: Path = DEFAULT_TEMPLATE_ROOT
    static_root: Path = DEFAULT_STATIC_ROOT
    migrations_root: Path = DEFAULT_MIGRATIONS_ROOT
    alembic_config: Path = DEFAULT_ALEMBIC_CONFIG
    csrf_token_secret: str = _GENERATE_LOCAL_CSRF_SECRET
    csrf_cookie_secure: bool | None = None
    identity_options: IdentityOptions = field(default_factory=IdentityOptions)
    static_url_path: str = "/static/"
    csrf_token_secret_configured: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        project_root = self.project_root.resolve()
        object.__setattr__(self, "project_root", project_root)
        if self.deployment_environment not in ALLOWED_DEPLOYMENT_ENVIRONMENTS:
            raise ConfigurationError(DEPLOYMENT_ENVIRONMENT_ERROR)
        csrf_cookie_secure = (
            self.deployment_environment != "local"
            if self.csrf_cookie_secure is None
            else self.csrf_cookie_secure
        )
        object.__setattr__(self, "csrf_cookie_secure", csrf_cookie_secure)
        csrf_secret_configured = self._csrf_secret_is_configured(self.csrf_token_secret)
        self._validate_identity_options(
            self.deployment_environment,
            self.identity_options,
        )
        self._validate_csrf_options(
            self.deployment_environment,
            csrf_secret_configured,
            csrf_cookie_secure,
        )
        if not csrf_secret_configured:
            logger.info(
                "Generated startup-local CSRF token secret. Configure "
                "csrf_token_secret for stable tokens across reloads or workers.",
                extra={"deployment_environment": self.deployment_environment},
            )
            object.__setattr__(
                self,
                "csrf_token_secret",
                token_urlsafe(CSRF_TOKEN_SECRET_BYTES),
            )
        object.__setattr__(
            self,
            "csrf_token_secret_configured",
            csrf_secret_configured,
        )
        object.__setattr__(
            self,
            "database_url",
            resolve_database_url(self.database_url, project_root),
        )
        object.__setattr__(
            self,
            "template_root",
            self._resolve_path(self.template_root, project_root, DEFAULT_TEMPLATE_ROOT),
        )
        object.__setattr__(
            self,
            "static_root",
            self._resolve_path(self.static_root, project_root, DEFAULT_STATIC_ROOT),
        )
        object.__setattr__(
            self,
            "migrations_root",
            self._resolve_path(
                self.migrations_root, project_root, DEFAULT_MIGRATIONS_ROOT
            ),
        )
        object.__setattr__(
            self,
            "alembic_config",
            self._resolve_path(
                self.alembic_config, project_root, DEFAULT_ALEMBIC_CONFIG
            ),
        )

    @staticmethod
    def _resolve_path(path: Path, project_root: Path, default_path: Path) -> Path:
        resolved_path = path or default_path
        if not resolved_path.is_absolute():
            resolved_path = project_root / resolved_path

        return resolved_path.resolve()

    @staticmethod
    def _validate_identity_options(
        deployment_environment: DeploymentEnvironment,
        identity_options: IdentityOptions,
    ) -> None:
        if deployment_environment != "local" and (
            is_generate_local_identity_secret(
                identity_options.reset_password_token_secret
            )
            or is_generate_local_identity_secret(
                identity_options.verification_token_secret
            )
        ):
            raise ConfigurationError(
                "Non-local deployments must not use generated local identity "
                "secret sentinels."
            )

        if (
            deployment_environment != "local"
            and not identity_options.token_secrets_configured
        ):
            raise ConfigurationError(
                "Non-local deployments must configure identity reset and "
                "verification token secrets."
            )

        if (
            deployment_environment != "local"
            and not identity_options.session_cookie_secure
        ):
            raise ConfigurationError(
                "Non-local deployments must use secure session cookies."
            )

    @staticmethod
    def _csrf_secret_is_configured(csrf_token_secret: str) -> bool:
        if csrf_token_secret == _GENERATE_LOCAL_CSRF_SECRET:
            return False

        if not csrf_token_secret.strip():
            raise ConfigurationError("CSRF token secret must not be blank.")

        return True

    @staticmethod
    def _validate_csrf_options(
        deployment_environment: DeploymentEnvironment,
        csrf_secret_configured: bool,
        csrf_cookie_secure: bool,
    ) -> None:
        if deployment_environment == "local":
            return

        if not csrf_secret_configured:
            raise ConfigurationError(
                "Non-local deployments must configure a stable CSRF token secret."
            )

        if not csrf_cookie_secure:
            raise ConfigurationError(
                "Non-local deployments must use secure CSRF cookies."
            )

    @property
    def static_mount_path(self) -> str:
        return f"/{self.static_url_path.strip('/')}"


def load_settings(
    *,
    environ: Mapping[str, str] | None = None,
    project_root: Path | None = None,
    read_dotenv: bool = True,
) -> Settings:
    """Build settings from envex-backed runtime configuration.

    Values loaded from the supplied environment mapping or process environment,
    plus `.env` when enabled, override `Settings` defaults. Callers that need
    fully explicit configuration should instantiate `Settings(...)` directly.

    The environment is copied before envex reads `.env`, so this function does
    not mutate `os.environ`. `project_root` is used as the dotenv search root and
    as the base for resolving relative configured paths and SQLite database URLs.
    """
    env = load_environment(
        environ=environ,
        project_root=project_root,
        read_dotenv=read_dotenv,
    )
    settings_kwargs: dict[str, Any] = {}
    if project_root is not None:
        settings_kwargs["project_root"] = project_root
    _set_env_fields(env, settings_kwargs, SETTINGS_ENV_SETTINGS)

    identity_options = _identity_options_from_environment(env)
    if identity_options is not None:
        settings_kwargs["identity_options"] = identity_options

    return Settings(**settings_kwargs)


def _identity_options_from_environment(env: Env) -> IdentityOptions | None:
    if not any(env.is_set(env_setting.name) for env_setting in IDENTITY_ENV_SETTINGS):
        return None

    identity_kwargs: dict[str, Any] = {}
    _set_env_fields(env, identity_kwargs, IDENTITY_ENV_SETTINGS)
    return IdentityOptions(**identity_kwargs)


def _set_env_fields(
    env: Env,
    values: dict[str, Any],
    env_settings: tuple[EnvironmentSetting, ...],
) -> None:
    for env_setting in env_settings:
        if env_setting.value_type == "path":
            _set_env_path(env, values, env_setting.field_name, env_setting.name)
        elif env_setting.value_type == "bool":
            _set_env_bool(env, values, env_setting.field_name, env_setting.name)
        elif env_setting.value_type == "int":
            _set_env_int(env, values, env_setting.field_name, env_setting.name)
        else:
            _set_env_value(env, values, env_setting.field_name, env_setting.name)


def _set_env_value(
    env: Env,
    values: dict[str, Any],
    setting_name: str,
    env_name: str,
    *,
    default: str | None = None,
) -> None:
    if env.is_set(env_name):
        _reject_blank_env_value(env, env_name)
        values[setting_name] = env.get(env_name)
    elif default is not None:
        values[setting_name] = default


def _set_env_path(
    env: Env,
    values: dict[str, Any],
    setting_name: str,
    env_name: str,
) -> None:
    if env.is_set(env_name):
        _reject_blank_env_value(env, env_name)
        values[setting_name] = Path(env.get(env_name))


def _set_env_bool(
    env: Env,
    values: dict[str, Any],
    setting_name: str,
    env_name: str,
) -> None:
    if env.is_set(env_name):
        _reject_blank_env_value(env, env_name)
        try:
            values[setting_name] = env.bool(env_name)
        except ValueError as exc:
            raise ConfigurationError(f"{env_name} must be a boolean value.") from exc


def _set_env_int(
    env: Env,
    values: dict[str, Any],
    setting_name: str,
    env_name: str,
) -> None:
    if env.is_set(env_name):
        _reject_blank_env_value(env, env_name)
        try:
            values[setting_name] = cast(int, env.int(env_name))
        except ValueError as exc:
            raise ConfigurationError(f"{env_name} must be an integer value.") from exc


def _reject_blank_env_value(env: Env, env_name: str) -> None:
    raw_value = env.get(env_name)
    if raw_value is None or not raw_value.strip():
        raise ConfigurationError(f"{env_name} must not be blank.")
