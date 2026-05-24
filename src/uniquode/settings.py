import logging
from dataclasses import dataclass, field
from pathlib import Path
from secrets import token_urlsafe
from typing import Literal

from uniquode.database_urls import (
    SQLITE_ASYNC_DATABASE_URL_PREFIX,
    SQLITE_MEMORY_DATABASE_URL,
    resolve_database_url,
)
from uniquode.identity.options import IdentityOptions

__all__ = (
    "DEFAULT_ALEMBIC_CONFIG",
    "DEFAULT_DATABASE_FILE",
    "DEFAULT_DATABASE_URL",
    "DEFAULT_MIGRATIONS_ROOT",
    "DEFAULT_STATIC_ROOT",
    "DEFAULT_TEMPLATE_ROOT",
    "DeploymentEnvironment",
    "SQLITE_ASYNC_DATABASE_URL_PREFIX",
    "SQLITE_MEMORY_DATABASE_URL",
    "Settings",
)

DeploymentEnvironment = Literal["local", "staging", "production"]

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
        if deployment_environment == "local":
            return

        if not identity_options.token_secrets_configured:
            raise ValueError(
                "Non-local deployments must configure identity reset and "
                "verification token secrets."
            )

    @staticmethod
    def _csrf_secret_is_configured(csrf_token_secret: str) -> bool:
        if csrf_token_secret == _GENERATE_LOCAL_CSRF_SECRET:
            return False

        if not csrf_token_secret.strip():
            raise ValueError("CSRF token secret must not be blank.")

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
            raise ValueError(
                "Non-local deployments must configure a stable CSRF token secret."
            )

        if not csrf_cookie_secure:
            raise ValueError("Non-local deployments must use secure CSRF cookies.")

    @property
    def static_mount_path(self) -> str:
        return f"/{self.static_url_path.strip('/')}"
