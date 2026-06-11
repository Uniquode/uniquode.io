import logging
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from secrets import token_urlsafe
from typing import Any, Final, Literal, cast, get_args

from envex import Env
from wevra.auth.options import (
    DEFAULT_SESSION_COOKIE_NAME as WEVRA_DEFAULT_SESSION_COOKIE_NAME,
)
from wevra.auth.options import (
    IdentityOptions,
    is_generate_local_identity_secret,
)
from wevra.auth.settings import (
    load_auth_settings,
    merge_identity_options_with_environment,
)
from wevra.config import AppConfigSource, ConfigService
from wevra.core.composition import (
    APP_CONFIG_ENV,
    DEFAULT_APP_CONFIG,
    AppConfig,
)
from wevra.core.diagnostics import wrapped_error
from wevra.core.settings import (
    SettingsLoadError,
    load_composition_config_from_environment,
    values_from_env_settings,
)
from wevra.db.urls import (
    SQLITE_ASYNC_DATABASE_URL_PREFIX,
    SQLITE_MEMORY_DATABASE_URL,
    resolve_database_url,
)
from wevra.web.security import CrossOriginOpenerPolicy

from app.config_definitions import (
    APP_CONFIG_SECTION,
    APP_STATIC_CONFIG_SECTION,
    APP_TEMPLATES_CONFIG_SECTION,
    ENV_DATABASE_URL,
    SETTINGS_ENV_SETTINGS,
    config_environment_names,
)
from app.configuration import ConfigurationError
from app.environment import (
    load_environment,
)

__all__ = (
    "DEFAULT_ALEMBIC_CONFIG",
    "DEFAULT_DATABASE_FILE",
    "DEFAULT_DATABASE_URL",
    "DEFAULT_MODULES",
    "DEFAULT_ROUTE_PREFIXES",
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

DEFAULT_ALEMBIC_CONFIG = Path("alembic.ini")
DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_FILE = Path("app.sqlite3")
DEFAULT_DATABASE_URL = (
    f"{SQLITE_ASYNC_DATABASE_URL_PREFIX}{DEFAULT_DATABASE_FILE.as_posix()}"
)
DEFAULT_MODULES: Final = ("app", "wevra.web", "wevra.auth")
DEFAULT_ROUTE_PREFIXES: Final[dict[str, dict[str, str]]] = {
    "app": {"default": ""},
    "wevra.web": {"partials": "", "api": ""},
    "wevra.auth": {"account": "/account", "api": ""},
}
DEFAULT_SESSION_COOKIE_NAME: Final = "uniquode_session"
CSRF_TOKEN_SECRET_BYTES = 32
_GENERATE_LOCAL_CSRF_SECRET = "__generate-local-csrf-secret__"

logger = logging.getLogger(__name__)


def _default_identity_options() -> IdentityOptions:
    return IdentityOptions(session_cookie_name=DEFAULT_SESSION_COOKIE_NAME)


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "uniquode"
    deployment_environment: DeploymentEnvironment = "local"
    database_url: str = DEFAULT_DATABASE_URL
    project_root: Path = field(default=DEFAULT_PROJECT_ROOT)
    template_root: Path | None = None
    static_root: Path | None = None
    migrations_root: Path | None = None
    alembic_config: Path = DEFAULT_ALEMBIC_CONFIG
    csrf_token_secret: str = _GENERATE_LOCAL_CSRF_SECRET
    csrf_cookie_secure: bool | None = None
    identity_options: IdentityOptions = field(default_factory=_default_identity_options)
    static_url_path: str = "/static/"
    template_auto_reload: bool | None = None
    template_cache_size: int = 400
    cross_origin_opener_policy: CrossOriginOpenerPolicy | None = "same-origin"
    app_config: AppConfig | None = None
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
        identity_options = self._normalise_identity_options(self.identity_options)
        object.__setattr__(self, "identity_options", identity_options)
        csrf_secret_configured = self._csrf_secret_is_configured(self.csrf_token_secret)
        if self.identity_enabled:
            self._validate_identity_options(
                self.deployment_environment,
                identity_options,
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
            self._resolve_optional_path(
                self.template_root,
                project_root,
                "template_root",
            ),
        )
        object.__setattr__(
            self,
            "static_root",
            self._resolve_optional_path(
                self.static_root,
                project_root,
                "static_root",
            ),
        )
        object.__setattr__(
            self,
            "migrations_root",
            self._resolve_optional_path(
                self.migrations_root,
                project_root,
                "migrations_root",
            ),
        )
        object.__setattr__(
            self,
            "alembic_config",
            self._resolve_path(
                self.alembic_config,
                project_root,
                DEFAULT_ALEMBIC_CONFIG,
                "alembic_config",
            ),
        )

    @staticmethod
    def _normalise_identity_options(
        identity_options: IdentityOptions,
    ) -> IdentityOptions:
        if identity_options.session_cookie_name != WEVRA_DEFAULT_SESSION_COOKIE_NAME:
            return identity_options

        normalised_options = replace(
            identity_options,
            session_cookie_name=DEFAULT_SESSION_COOKIE_NAME,
        )
        object.__setattr__(
            normalised_options,
            "token_secrets_configured",
            identity_options.token_secrets_configured,
        )
        return normalised_options

    @staticmethod
    def _resolve_optional_path(
        path: Path | str | None,
        project_root: Path,
        setting_name: str,
    ) -> Path | None:
        if path is None:
            return None
        if isinstance(path, str):
            if not path.strip():
                raise ConfigurationError(f"{setting_name} must not be blank.")
            resolved_path = Path(path)
        else:
            resolved_path = path

        if not resolved_path.is_absolute():
            resolved_path = project_root / resolved_path

        return resolved_path.resolve()

    @staticmethod
    def _resolve_path(
        path: Path | str | None,
        project_root: Path,
        default_path: Path,
        setting_name: str,
    ) -> Path:
        resolved_path = Settings._resolve_optional_path(
            path,
            project_root,
            setting_name,
        )
        if resolved_path is None:
            resolved_path = default_path
            if not resolved_path.is_absolute():
                resolved_path = project_root / resolved_path
            return resolved_path.resolve()

        return resolved_path

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
            and not identity_options.session_cookie_force_secure
        ):
            raise ConfigurationError(
                "Non-local deployments must force secure session cookies; set "
                "SESSION_FORCE_SECURE=true or auth.session_cookie_force_secure = true."
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

    @property
    def uses_filesystem_template_root(self) -> bool:
        return self.template_root is not None

    @property
    def uses_filesystem_static_root(self) -> bool:
        return self.static_root is not None

    @property
    def modules(self) -> tuple[str, ...]:
        if self.app_config is None:
            return DEFAULT_MODULES

        return self.app_config.modules

    @property
    def route_prefixes(self) -> dict[str, dict[str, str]]:
        prefixes = {
            module: dict(DEFAULT_ROUTE_PREFIXES[module])
            for module in self.modules
            if module in DEFAULT_ROUTE_PREFIXES
        }
        if self.app_config is not None:
            for module, configured_prefixes in self.app_config.routes.prefixes.items():
                prefixes[module] = {
                    **prefixes.get(module, {}),
                    **configured_prefixes,
                }

        return prefixes

    @property
    def identity_enabled(self) -> bool:
        return "wevra.auth" in self.modules


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
    resolved_project_root = (project_root or DEFAULT_PROJECT_ROOT).resolve()
    try:
        env = load_environment(
            environ=environ,
            project_root=resolved_project_root,
            read_dotenv=read_dotenv,
        )
        app_config = load_composition_config_from_environment(
            env,
            project_root=resolved_project_root,
            app_config_env=APP_CONFIG_ENV,
            default_app_config=DEFAULT_APP_CONFIG,
            require_app_config=True,
        )
        if app_config is None:  # pragma: no cover - require_app_config prevents this
            raise ConfigurationError(
                "Application config file could not be resolved; run from the "
                f"app project or set {APP_CONFIG_ENV}."
            )
        config = ConfigService(
            [AppConfigSource(app_config)],
            environ=_environment_mapping(env),
        )
        return Settings(**_settings_kwargs_from_config(config, app_config, env))
    except SettingsLoadError as exc:
        raise wrapped_error(ConfigurationError, exc) from exc


def _settings_kwargs_from_config(
    config: ConfigService,
    app_config: AppConfig,
    env: Env,
) -> dict[str, Any]:
    app_values = dict(config.get_config(APP_CONFIG_SECTION) or {})
    static_values = dict(config.get_config(APP_STATIC_CONFIG_SECTION) or {})
    template_values = dict(config.get_config(APP_TEMPLATES_CONFIG_SECTION) or {})
    env_values = values_from_env_settings(env, SETTINGS_ENV_SETTINGS)
    auth_settings = load_auth_settings(
        app_config=app_config,
        environ=_auth_database_environment(app_values),
    )
    database_url = _configured_database_url(
        app_values,
        fallback=auth_settings.database_url,
    )
    settings_kwargs: dict[str, Any] = {
        "project_root": app_config.project_root,
        "app_config": app_config,
        "database_url": database_url,
        "identity_options": merge_identity_options_with_environment(
            auth_settings.identity_options,
            app_config.auth,
            env,
        ),
        "static_url_path": static_values.get("url_path", app_config.static.url_path),
        "template_auto_reload": template_values.get(
            "auto_reload",
            app_config.templates.auto_reload,
        ),
        "template_cache_size": template_values.get(
            "cache_size",
            app_config.templates.cache_size,
        ),
    }
    for field_name in (
        "alembic_config",
        "app_name",
        "csrf_cookie_secure",
        "csrf_token_secret",
        "deployment_environment",
        "migrations_root",
    ):
        if field_name in app_values:
            settings_kwargs[field_name] = app_values[field_name]
    if "root" in static_values:
        settings_kwargs["static_root"] = static_values["root"]
    if "root" in template_values:
        settings_kwargs["template_root"] = template_values["root"]
    settings_kwargs.update(env_values)
    return settings_kwargs


def _auth_database_environment(app_values: Mapping[str, Any]) -> dict[str, str]:
    database_url = _configured_database_url(app_values)
    return {ENV_DATABASE_URL: database_url} if database_url is not None else {}


def _configured_database_url(
    app_values: Mapping[str, Any],
    *,
    fallback: str | None = None,
) -> str | None:
    database_url = app_values.get("database_url")
    if not isinstance(database_url, str) or not database_url.strip():
        return fallback
    return database_url


def _environment_mapping(env: Env) -> dict[str, str]:
    names = config_environment_names()
    return {
        name: value
        for name in names
        if env.is_set(name) and (value := env.get(name)) is not None
    }
