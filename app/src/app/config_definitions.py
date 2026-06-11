from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from wevra.config import ConfigDef, ConfigSection
from wevra.core.settings import EnvironmentSetting

APP_CONFIG_SECTION: Final = "app"
APP_STATIC_CONFIG_SECTION: Final = "app.static"
APP_TEMPLATES_CONFIG_SECTION: Final = "app.templates"

ENV_ALEMBIC_CONFIG: Final = "ALEMBIC_CONFIG"
ENV_APP_ENV: Final = "APP_ENV"
ENV_APP_NAME: Final = "APP_NAME"
ENV_CSRF_SECRET: Final = "CSRF_SECRET"
ENV_CSRF_SECURE: Final = "CSRF_SECURE"
ENV_DATABASE_URL: Final = "DATABASE_URL"
ENV_MIGRATIONS_ROOT: Final = "MIGRATIONS_ROOT"
ENV_STATIC_ROOT: Final = "STATIC_ROOT"
ENV_STATIC_URL: Final = "STATIC_URL"
ENV_TEMPLATE_ROOT: Final = "TEMPLATE_ROOT"

EnvironmentSettingKind = Literal["str", "bool", "int", "path"]


@dataclass(frozen=True, slots=True)
class ConfigEnvField:
    section: str
    config_field: str
    env_name: str
    settings_field: str
    kind: EnvironmentSettingKind = "str"

    def environment_setting(self) -> EnvironmentSetting:
        return EnvironmentSetting(
            self.env_name,
            self.settings_field,
            self.kind,
        )


APP_CONFIG_ENV_FIELDS: Final = (
    ConfigEnvField(
        APP_CONFIG_SECTION,
        "alembic_config",
        ENV_ALEMBIC_CONFIG,
        "alembic_config",
        "path",
    ),
    ConfigEnvField(
        APP_CONFIG_SECTION,
        "app_name",
        ENV_APP_NAME,
        "app_name",
    ),
    ConfigEnvField(
        APP_CONFIG_SECTION,
        "csrf_cookie_secure",
        ENV_CSRF_SECURE,
        "csrf_cookie_secure",
        "bool",
    ),
    ConfigEnvField(
        APP_CONFIG_SECTION,
        "csrf_token_secret",
        ENV_CSRF_SECRET,
        "csrf_token_secret",
    ),
    ConfigEnvField(
        APP_CONFIG_SECTION,
        "database_url",
        ENV_DATABASE_URL,
        "database_url",
    ),
    ConfigEnvField(
        APP_CONFIG_SECTION,
        "deployment_environment",
        ENV_APP_ENV,
        "deployment_environment",
    ),
    ConfigEnvField(
        APP_CONFIG_SECTION,
        "migrations_root",
        ENV_MIGRATIONS_ROOT,
        "migrations_root",
        "path",
    ),
    ConfigEnvField(
        APP_STATIC_CONFIG_SECTION,
        "root",
        ENV_STATIC_ROOT,
        "static_root",
        "path",
    ),
    ConfigEnvField(
        APP_STATIC_CONFIG_SECTION,
        "url_path",
        ENV_STATIC_URL,
        "static_url_path",
    ),
    ConfigEnvField(
        APP_TEMPLATES_CONFIG_SECTION,
        "root",
        ENV_TEMPLATE_ROOT,
        "template_root",
        "path",
    ),
)

SETTINGS_ENV_SETTINGS: Final[tuple[EnvironmentSetting, ...]] = tuple(
    field.environment_setting() for field in APP_CONFIG_ENV_FIELDS
)

module_config = ConfigDef(
    {
        APP_CONFIG_SECTION: ConfigSection(
            fields={
                "alembic_config",
                "app_name",
                "csrf_cookie_secure",
                "csrf_token_secret",
                "database_url",
                "deployment_environment",
                "migrations_root",
            },
            defaults={
                "app_name": "uniquode",
                "database_url": "sqlite+aiosqlite:///app.sqlite3",
                "deployment_environment": "local",
            },
            env={
                field.config_field: field.env_name
                for field in APP_CONFIG_ENV_FIELDS
                if field.section == APP_CONFIG_SECTION
            },
        ),
        APP_STATIC_CONFIG_SECTION: ConfigSection(
            fields={"root", "url_path"},
            defaults={"url_path": "/static/"},
            env={
                field.config_field: field.env_name
                for field in APP_CONFIG_ENV_FIELDS
                if field.section == APP_STATIC_CONFIG_SECTION
            },
        ),
        APP_TEMPLATES_CONFIG_SECTION: ConfigSection(
            fields={"auto_reload", "cache_size", "root"},
            env={
                field.config_field: field.env_name
                for field in APP_CONFIG_ENV_FIELDS
                if field.section == APP_TEMPLATES_CONFIG_SECTION
            },
        ),
    }
)


def config_environment_names(config_def: ConfigDef = module_config) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for section in config_def.sections.values():
        for env_names in section.env.values():
            for env_name in env_names:
                if env_name not in seen:
                    seen.add(env_name)
                    names.append(env_name)
    return tuple(names)
