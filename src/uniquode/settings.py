import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from secrets import token_urlsafe
from typing import Final, Literal, cast, get_args

from envex import Env

import data_core
import web_core
from auth_ext.options import (
    IdentityOptions,
    is_generate_local_identity_secret,
)
from data_core.database_urls import (
    SQLITE_ASYNC_DATABASE_URL_PREFIX,
    SQLITE_MEMORY_DATABASE_URL,
    resolve_database_url,
)
from uniquode.configuration import ConfigurationError
from uniquode.environment import (
    IDENTITY_ENV_SETTINGS,
    SETTINGS_ENV_SETTINGS,
    load_environment,
)
from web_core.composition import (
    AppConfig,
)
from web_core.diagnostics import wrapped_error
from web_core.settings import (
    SettingsLoadError,
    env_setting_is_set,
    load_composed_settings,
    values_from_env_settings,
)

__all__ = (
    "DEFAULT_ALEMBIC_CONFIG",
    "DEFAULT_DATABASE_FILE",
    "DEFAULT_DATABASE_URL",
    "DEFAULT_MODULES",
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

_DATA_CORE_PACKAGE_ROOT = Path(data_core.__file__).resolve().parent
_WEB_CORE_PACKAGE_ROOT = Path(web_core.__file__).resolve().parent
DEFAULT_TEMPLATE_ROOT = _WEB_CORE_PACKAGE_ROOT / "templates"
DEFAULT_STATIC_ROOT = _WEB_CORE_PACKAGE_ROOT / "static"
DEFAULT_MIGRATIONS_ROOT = _DATA_CORE_PACKAGE_ROOT / "migrations"
DEFAULT_ALEMBIC_CONFIG = Path("alembic.ini")
DEFAULT_DATABASE_FILE = Path("uniquode.sqlite3")
DEFAULT_DATABASE_URL = (
    f"{SQLITE_ASYNC_DATABASE_URL_PREFIX}{DEFAULT_DATABASE_FILE.as_posix()}"
)
DEFAULT_MODULES: Final = ("web_core", "public", "uniquode", "auth_ext")
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
    template_auto_reload: bool | None = None
    template_cache_size: int = 400
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
        csrf_secret_configured = self._csrf_secret_is_configured(self.csrf_token_secret)
        if self.identity_enabled:
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
            self._resolve_path(
                self.template_root,
                project_root,
                DEFAULT_TEMPLATE_ROOT,
                "template_root",
            ),
        )
        object.__setattr__(
            self,
            "static_root",
            self._resolve_path(
                self.static_root,
                project_root,
                DEFAULT_STATIC_ROOT,
                "static_root",
            ),
        )
        object.__setattr__(
            self,
            "migrations_root",
            self._resolve_path(
                self.migrations_root,
                project_root,
                DEFAULT_MIGRATIONS_ROOT,
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
    def _resolve_path(
        path: Path | str | None,
        project_root: Path,
        default_path: Path,
        setting_name: str,
    ) -> Path:
        if path is None:
            resolved_path = default_path
        elif isinstance(path, str):
            if not path.strip():
                raise ConfigurationError(f"{setting_name} must not be blank.")
            resolved_path = Path(path)
        else:
            resolved_path = path

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

    @staticmethod
    def _normalised_path(path: Path) -> Path:
        try:
            return path.resolve(strict=False)
        except (OSError, RuntimeError):
            return path.absolute()

    @classmethod
    def _paths_refer_to_same_location(cls, left: Path, right: Path) -> bool:
        try:
            return left.samefile(right)
        except (OSError, RuntimeError):
            return cls._normalised_path(left) == cls._normalised_path(right)

    @property
    def uses_filesystem_template_root(self) -> bool:
        return not self._paths_refer_to_same_location(
            self.template_root,
            DEFAULT_TEMPLATE_ROOT,
        )

    @property
    def uses_filesystem_static_root(self) -> bool:
        return not self._paths_refer_to_same_location(
            self.static_root,
            DEFAULT_STATIC_ROOT,
        )

    @property
    def modules(self) -> tuple[str, ...]:
        if self.app_config is None:
            return DEFAULT_MODULES

        return self.app_config.modules

    @property
    def identity_enabled(self) -> bool:
        return "auth_ext" in self.modules


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
    try:
        return load_composed_settings(
            Settings,
            environment_loader=load_environment,
            env_settings=SETTINGS_ENV_SETTINGS,
            extra_value_loaders=(_identity_options_kwargs_from_environment,),
            environ=environ,
            project_root=project_root,
            read_dotenv=read_dotenv,
        )
    except SettingsLoadError as exc:
        raise wrapped_error(ConfigurationError, exc) from exc


def _identity_options_kwargs_from_environment(env: Env) -> dict[str, IdentityOptions]:
    if not env_setting_is_set(env, IDENTITY_ENV_SETTINGS):
        return {}

    return {
        "identity_options": IdentityOptions(
            **values_from_env_settings(env, IDENTITY_ENV_SETTINGS)
        )
    }
