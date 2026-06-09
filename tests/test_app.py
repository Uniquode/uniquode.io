import asyncio
import importlib
import inspect
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import tomllib
from dataclasses import fields
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent

import click
import pytest
import wevra.auth.sessions as identity_users
import wevra.db.migrate as data_migrate_module
import wevra.tools.migrate as migrate_module
import wevra.tools.routes as routes_module
import wevra.tools.runserver as runserver_module
from fastapi import FastAPI, HTTPException, Request
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.exceptions import InvalidPasswordException
from sqlalchemy import MetaData, func, select, text
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from starlette.staticfiles import StaticFiles
from wevra.auth import (
    ERROR_ALREADY_EXISTS,
    ERROR_IDENTITY_CHANGED,
    ERROR_INACTIVE_USER,
    ERROR_INVALID_EMAIL,
    ERROR_INVALID_PASSWORD,
    ERROR_INVALID_TOKEN,
    ERROR_PASSWORD_TOO_SHORT,
    ERROR_PASSWORD_TOO_WEAK,
    PasswordStrength,
    Result,
)
from wevra.auth.accounts.bootstrap import (
    InitialAdminCredentials,
    bootstrap_initial_admin,
)
from wevra.auth.accounts.schemas import UserCreate
from wevra.auth.models import (
    AccessToken,
    Base,
    ExternalIdentityLink,
    IdentityProvider,
    InitialAdminBootstrap,
    User,
)
from wevra.auth.models import (
    metadata as wevra_auth_metadata,
)
from wevra.auth.options import (
    DEFAULT_SESSION_COOKIE_NAME as WEVRA_DEFAULT_SESSION_COOKIE_NAME,
)
from wevra.auth.options import (
    PASSKEY,
    PROVIDER,
    TOTP,
    VALID_IDENTITY_INTEGRATIONS,
    IdentityOptions,
    identity_env_setting_name,
)
from wevra.auth.sessions import (
    create_authentication_backend,
    create_database_strategy,
    create_user_manager,
    require_anonymous_user,
    require_current_user,
    session_cookie_secure_for_request,
)
from wevra.auth.settings import (
    ENV_ACCOUNT_CREATION_POLICY,
    ENV_RESET_SECRET,
    ENV_SESSION_COOKIE,
    ENV_SESSION_FORCE_SECURE,
    ENV_SESSION_LIFETIME,
    ENV_VERIFICATION_SECRET,
)
from wevra.core.composition import (
    AppConfig,
    CompositionError,
    RouteOptions,
    StaticOptions,
    TemplateOptions,
)
from wevra.db.migration_metadata import (
    MigrationConfigError,
    load_model_metadata,
    model_packages_from_modules,
)
from wevra.db.persistence import (
    Database,
    close_database,
    create_database,
    create_database_engine,
    create_session_factory,
    is_supported_database_url,
    session_scope,
    sqlite_database_path,
)
from wevra.db.surfaces import DataCompositionError
from wevra.tools.project import (
    ProjectToolConfigurationError,
    import_from_string,
    runtime_project_root,
)
from wevra.tools.runserver import (
    APP_TARGET_OPTION,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_RELOAD,
    RELOAD_ENV_VAR_OPTION,
    env_requests_reload,
)
from wevra.web.context import get_request_context
from wevra.web.errors import EmptyBodyResponseException
from wevra.web.forms.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_FIELD_NAME,
    CSRF_HEADER_NAME,
)
from wevra.web.routes.contracts import _normalise_path_prefix
from wevra.web.security import COOP_HEADER_NAME
from wevra.web.staticfiles import ComposedStaticFiles, NoStaticFiles

import app.asgi as asgi_module
import app.environment as environment_module
from app.app import create_app
from app.asgi import app
from app.configuration import ConfigurationError
from app.environment import (
    ENV_ALEMBIC_CONFIG,
    ENV_APP_CONFIG,
    ENV_APP_ENV,
    ENV_APP_NAME,
    ENV_APP_RELOAD,
    ENV_CSRF_SECRET,
    ENV_CSRF_SECURE,
    ENV_DATABASE_URL,
    ENV_MIGRATIONS_ROOT,
    ENV_STATIC_ROOT,
    ENV_STATIC_URL,
    ENV_TEMPLATE_ROOT,
    IDENTITY_ENV_SETTINGS,
    load_environment,
)
from app.routes.health import health
from app.settings import (
    DEFAULT_ROUTE_PREFIXES,
    SQLITE_MEMORY_DATABASE_URL,
    Settings,
    load_settings,
)

CSRF_INPUT_PATTERN = re.compile(
    rf'<input[^>]+name="{CSRF_FIELD_NAME}"[^>]+value="([^"]+)"'
)


DEFAULT_IDENTITY_INTEGRATION_FLAGS = {
    integration: False for integration in VALID_IDENTITY_INTEGRATIONS
}


def assert_identity_integration_flags(
    options: IdentityOptions,
    integration_flags: dict[str, bool],
) -> None:
    for integration, expected in integration_flags.items():
        assert options.integration_enabled(integration) is expected


IDENTITY_TABLE_NAMES = frozenset(
    {
        "identity_user",
        "identity_access_token",
        "identity_provider",
        "identity_external_identity_link",
    },
)


def assert_identity_tables_present(table_names: set[str]) -> None:
    assert IDENTITY_TABLE_NAMES.issubset(table_names)


def sqlite_file_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.resolve().as_posix()}"


def write_wevra_tool_config(path: Path) -> Path:
    path.write_text(
        """
        [tool.wevra]
        settings_loader = "app.settings:load_settings"
        configuration_error = "app.configuration:ConfigurationError"
        environment_loader = "app.environment:load_environment"
        database_url_env = "DATABASE_URL"
        runserver_reload_env = "APP_RELOAD"
        runserver_app = "app.asgi:app"
        """,
        encoding="utf-8",
    )
    return path


def write_app_config(
    path: Path,
    *,
    modules: tuple[str, ...] = ("app", "wevra.web", "wevra.auth"),
    route_prefixes: dict[str, dict[str, str]] | None = None,
    static_url_path: str = "/static/",
    static_export_root: str = "static",
    database_url: str = "sqlite+aiosqlite:///app.sqlite3",
    auth_options: dict[str, object] | None = None,
) -> Path:
    prefixes = {
        module_name: dict(DEFAULT_ROUTE_PREFIXES[module_name])
        for module_name in modules
        if module_name in DEFAULT_ROUTE_PREFIXES
    }
    if route_prefixes is not None:
        for module, labels in route_prefixes.items():
            prefixes[module] = {**prefixes.get(module, {}), **labels}

    missing_prefix_modules = tuple(
        module_name for module_name in modules if module_name not in prefixes
    )
    if missing_prefix_modules:
        raise ValueError(
            "write_app_config needs explicit route_prefixes for modules without "
            f"test defaults: {', '.join(missing_prefix_modules)}"
        )

    route_config = "\n".join(
        (
            f"{module_name.replace('.', '-')} = "
            "{ "
            + ", ".join(
                f"{json.dumps(label)} = {json.dumps(prefix)}"
                for label, prefix in prefixes[module_name].items()
            )
            + " }"
        )
        for module_name in modules
    )
    auth_config = "\n".join(
        f"{key} = {json.dumps(value)}" for key, value in (auth_options or {}).items()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""
        [app]
        database_url = {json.dumps(database_url)}
        modules = {json.dumps(list(modules))}

        [app.routes]
        {route_config}

        [app.templates]
        auto_reload = true
        cache_size = 0

        [app.static]
        url_path = {json.dumps(static_url_path)}
        export_root = {json.dumps(static_export_root)}

        [auth]
        session_cookie_force_secure = false
        {auth_config}

        [auth.password.policy]
        minimum_length = 12
        minimum_character_categories = 2
        minimum_strength = 0.45
        common_fragments = ["admin", "password", "test"]
        """,
        encoding="utf-8",
    )
    return path


def test_write_app_config_requires_route_prefixes_for_modules_without_defaults(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="custom_route_app",
    ):
        write_app_config(tmp_path / "app.toml", modules=("custom_route_app",))


def test_write_app_config_writes_hyphenated_route_module_alias_and_labels(
    tmp_path: Path,
) -> None:
    config_path = write_app_config(
        tmp_path / "app.toml",
        modules=("custom.route.app",),
        route_prefixes={"custom.route.app": {"api-v2": "/api/v2"}},
    )

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    assert data["app"]["routes"]["custom-route-app"]["api-v2"] == "/api/v2"


def build_test_app_config(
    root: Path,
    *,
    modules: tuple[str, ...],
    route_prefixes: dict[str, dict[str, str]] | None = None,
) -> AppConfig:
    prefixes = {
        module_name: dict(DEFAULT_ROUTE_PREFIXES[module_name])
        for module_name in modules
        if module_name in DEFAULT_ROUTE_PREFIXES
    }
    if route_prefixes is not None:
        for module, labels in route_prefixes.items():
            prefixes[module] = {**prefixes.get(module, {}), **labels}

    return AppConfig(
        config_path=(root / "app.toml").resolve(),
        project_root=root.resolve(),
        modules=modules,
        routes=RouteOptions(prefixes=prefixes),
        templates=TemplateOptions(auto_reload=True, cache_size=0),
        static=StaticOptions(url_path="/static/", export_root=Path("static")),
    )


def test_asgi_app_imports() -> None:
    assert isinstance(app, FastAPI)


def test_asgi_loader_reports_configuration_errors_without_traceback(
    monkeypatch,
    capsys,
) -> None:
    def raise_configuration_error():
        raise ConfigurationError("APP_ENV must be local, staging, or production.")

    monkeypatch.setattr(asgi_module, "create_app", raise_configuration_error)

    with pytest.raises(SystemExit) as excinfo:
        asgi_module.load_asgi_app()

    message = (
        "Application configuration failed: "
        "APP_ENV must be local, staging, or production."
    )
    captured = capsys.readouterr()
    assert str(excinfo.value) == message
    assert captured.err.strip() == message
    assert "Traceback" not in captured.err


def test_create_app_returns_fresh_app_with_baseline_routes() -> None:
    first = create_app()
    second = create_app()

    assert isinstance(first, FastAPI)
    assert isinstance(second, FastAPI)
    assert first is not second
    assert any(
        isinstance(route, APIRoute) and route.path == "/health"
        for route in first.routes
    )


def test_baseline_route_handlers_are_async() -> None:
    assert inspect.iscoroutinefunction(health)


def test_app_project_does_not_redeclare_wevra_operator_scripts() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"

    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)

    scripts = data["project"].get("scripts", {})
    wevra_operator_scripts = {
        "identitymgr",
        "migrate",
        "routes",
        "runserver",
        "validate",
        "wevra-authmgr",
        "wevra-identitymgr",
        "wevra-migrate",
        "wevra-routes",
        "wevra-runserver",
        "wevra-validate",
    }

    assert scripts.keys().isdisjoint(wevra_operator_scripts)


def test_wevra_db_migrate_requires_injected_settings_loader(capsys) -> None:
    exit_code = data_migrate_module.main(["current"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "configuration: failed" in captured.err
    assert "Migration settings loader is not configured." in captured.err


def test_project_tool_import_spec_requires_string() -> None:
    with pytest.raises(
        ProjectToolConfigurationError,
        match="Import spec must be configured as a string, got 'int'\\.",
    ):
        import_from_string(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("entrypoint", "argv", "help_text"),
    [
        (runserver_module.main, ["--help"], "Start the local Uvicorn"),
        (routes_module.main, ["--help"], "Inspect the configured application's"),
        (migrate_module.main, ["--help"], "Run application schema migrations"),
    ],
)
def test_click_backed_cli_help_returns_cleanly(
    capsys,
    entrypoint,
    argv: list[str],
    help_text: str,
) -> None:
    result = entrypoint(argv)

    captured = capsys.readouterr()
    assert result in {None, 0}
    assert help_text in captured.out
    assert captured.err == ""


@pytest.mark.parametrize(
    ("command", "entrypoint"),
    [
        (runserver_module.runserver_command, runserver_module.main),
        (migrate_module.migrate_command, migrate_module.main),
    ],
)
def test_click_backed_cli_main_treats_falsy_click_exception_as_failure(
    monkeypatch,
    capsys,
    command,
    entrypoint,
) -> None:
    class FalsyExitClickException(click.ClickException):
        exit_code = 0

    def raise_click_exception(*_args, **_kwargs) -> None:
        raise FalsyExitClickException("invalid usage")

    monkeypatch.setattr(command, "main", raise_click_exception)

    assert entrypoint([]) == 1

    captured = capsys.readouterr()
    assert "invalid usage" in captured.err


def test_migrate_upgrade_uses_settings_database_url(
    tmp_path,
    monkeypatch,
) -> None:
    calls: list[tuple[str, str, str]] = []

    def record_upgrade(config, revision: str) -> None:
        calls.append(
            (
                "upgrade",
                revision,
                config.get_main_option("sqlalchemy.url"),
            )
        )

    monkeypatch.setattr(migrate_module.command, "upgrade", record_upgrade)
    monkeypatch.setattr(
        data_migrate_module,
        "_migration_state_from_connection",
        lambda _database_url: data_migrate_module.MigrationState(initialised=True),
    )
    with sqlite3.connect(tmp_path / "app.sqlite3") as connection:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32))")
    write_wevra_tool_config(tmp_path / "pyproject.toml")
    write_app_config(tmp_path / "app.toml")
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)

    exit_code = migrate_module.main(["upgrade"])

    assert exit_code == 0
    assert calls == [
        (
            "upgrade",
            "head",
            sqlite_file_url(tmp_path / "app.sqlite3"),
        )
    ]


def test_migrate_database_url_override_takes_precedence(
    tmp_path,
    monkeypatch,
) -> None:
    calls: list[tuple[str, str | None]] = []

    def record_current(config) -> None:
        calls.append(("current", config.get_main_option("sqlalchemy.url")))

    monkeypatch.setattr(migrate_module.command, "current", record_current)
    monkeypatch.setattr(
        data_migrate_module,
        "inspect_migration_state",
        lambda _database_url: data_migrate_module.MigrationState(
            initialised=True,
            current_revisions=("abc123",),
        ),
    )
    write_wevra_tool_config(tmp_path / "pyproject.toml")
    write_app_config(tmp_path / "app.toml")
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)

    exit_code = migrate_module.main(
        [
            "--database-url",
            "sqlite+aiosqlite:///override.sqlite3",
            "current",
        ]
    )

    assert exit_code == 0
    assert calls == [
        (
            "current",
            sqlite_file_url(tmp_path / "override.sqlite3"),
        )
    ]


def test_migrate_alembic_config_accepts_percent_encoded_database_url() -> None:
    database_url = (
        "postgresql+asyncpg://db.example.test/uniquode?application_name=app%40local"
    )

    config = migrate_module.build_alembic_config(Settings(database_url=database_url))

    assert config.get_main_option("sqlalchemy.url") == database_url
    assert config.get_main_option("script_location") == "wevra.db:migrations"


def test_migrate_database_url_override_preempts_blank_environment_value(
    tmp_path,
    monkeypatch,
) -> None:
    calls: list[tuple[str, str | None]] = []

    def record_current(config) -> None:
        calls.append(("current", config.get_main_option("sqlalchemy.url")))

    monkeypatch.setattr(migrate_module.command, "current", record_current)
    monkeypatch.setattr(
        data_migrate_module,
        "inspect_migration_state",
        lambda _database_url: data_migrate_module.MigrationState(
            initialised=True,
            current_revisions=("abc123",),
        ),
    )
    write_wevra_tool_config(tmp_path / "pyproject.toml")
    write_app_config(tmp_path / "app.toml")
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)
    monkeypatch.setenv(ENV_DATABASE_URL, "")

    exit_code = migrate_module.main(
        [
            "--database-url",
            "sqlite+aiosqlite:///scratch.sqlite3",
            "current",
        ]
    )

    assert exit_code == 0
    assert calls == [
        (
            "current",
            sqlite_file_url(tmp_path / "scratch.sqlite3"),
        )
    ]


def test_migrate_database_url_override_can_follow_subcommand(
    tmp_path,
    monkeypatch,
) -> None:
    calls: list[tuple[str, str | None]] = []

    def record_upgrade(config, revision: str) -> None:
        calls.append((revision, config.get_main_option("sqlalchemy.url")))

    monkeypatch.setattr(migrate_module.command, "upgrade", record_upgrade)
    monkeypatch.setattr(
        data_migrate_module,
        "_migration_state_from_connection",
        lambda _database_url: data_migrate_module.MigrationState(initialised=True),
    )
    with sqlite3.connect(tmp_path / "subcommand.sqlite3") as connection:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32))")
    write_wevra_tool_config(tmp_path / "pyproject.toml")
    write_app_config(tmp_path / "app.toml")
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)

    exit_code = migrate_module.main(
        [
            "upgrade",
            "--database-url",
            "sqlite+aiosqlite:///subcommand.sqlite3",
        ]
    )

    assert exit_code == 0
    assert calls == [
        (
            "head",
            sqlite_file_url(tmp_path / "subcommand.sqlite3"),
        )
    ]


def test_migrate_rejects_blank_database_url_override(capsys) -> None:
    exit_code = migrate_module.main(["--database-url", "", "current"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "DATABASE_URL must not be blank" in captured.err


def test_migrate_rejects_invalid_root_database_url_context() -> None:
    ctx = click.Context(
        migrate_module.migrate_command,
        obj={"database_url": Path("not-a-string.sqlite3")},
    )

    with pytest.raises(click.UsageError, match="Invalid root database_url type"):
        migrate_module._database_url_for_command(ctx, None)


def test_migrate_rejects_invalid_context_object_shape() -> None:
    ctx = click.Context(migrate_module.migrate_command, obj="not-a-dict")

    with pytest.raises(click.UsageError, match="expected a dictionary"):
        migrate_module._database_url_for_command(ctx, None)


@pytest.mark.parametrize(
    "exception",
    [
        migrate_module.AlembicError("bad migration revision"),
        migrate_module.SQLAlchemyError("database unavailable"),
    ],
)
def test_migrate_reports_operation_errors_cleanly(
    tmp_path,
    monkeypatch,
    capsys,
    exception: Exception,
) -> None:
    def fail_current(_config) -> None:
        raise exception

    monkeypatch.setattr(migrate_module.command, "current", fail_current)
    monkeypatch.setattr(
        data_migrate_module,
        "inspect_migration_state",
        lambda _database_url: data_migrate_module.MigrationState(
            initialised=True,
            current_revisions=("abc123",),
        ),
    )
    write_wevra_tool_config(tmp_path / "pyproject.toml")
    write_app_config(tmp_path / "app.toml")
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)

    exit_code = migrate_module.main(["current"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "migration: failed" in captured.err
    assert str(exception) in captured.err


def test_migrate_reports_metadata_configuration_errors_cleanly(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    def fail_current(_config) -> None:
        raise MigrationConfigError("bad module metadata")

    monkeypatch.setattr(migrate_module.command, "current", fail_current)
    monkeypatch.setattr(
        data_migrate_module,
        "inspect_migration_state",
        lambda _database_url: data_migrate_module.MigrationState(
            initialised=True,
            current_revisions=("abc123",),
        ),
    )
    write_wevra_tool_config(tmp_path / "pyproject.toml")
    write_app_config(tmp_path / "app.toml")
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)

    exit_code = migrate_module.main(["current"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "configuration: failed" in captured.err
    assert "bad module metadata" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("argv", "command_name", "revision"),
    [
        (["downgrade", "base"], "downgrade", "base"),
        (["history"], "history", None),
    ],
)
def test_migrate_dispatches_supported_commands(
    tmp_path,
    monkeypatch,
    argv: list[str],
    command_name: str,
    revision: str | None,
) -> None:
    calls: list[tuple[str, str | None, str | None]] = []

    def record_command(config, revision_arg: str | None = None) -> None:
        calls.append(
            (
                command_name,
                revision_arg,
                config.get_main_option("sqlalchemy.url"),
            )
        )

    monkeypatch.setattr(migrate_module.command, command_name, record_command)
    write_wevra_tool_config(tmp_path / "pyproject.toml")
    write_app_config(tmp_path / "app.toml")
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)

    exit_code = migrate_module.main(argv)

    assert exit_code == 0
    assert calls == [
        (
            command_name,
            revision,
            sqlite_file_url(tmp_path / "app.sqlite3"),
        )
    ]


def test_migrate_init_then_upgrade_initialises_empty_sqlite_database(tmp_path) -> None:
    database_path = tmp_path / "dev.sqlite3"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"

    assert migrate_module.main(["--database-url", database_url, "init"]) == 0
    assert database_path.is_file()

    settings = Settings(database_url=database_url)
    engine = create_database_engine(settings)

    async def table_names() -> set[str]:
        async with engine.begin() as connection:
            return set(
                await connection.run_sync(
                    lambda sync_connection: sqlalchemy_inspect(
                        sync_connection
                    ).get_table_names()
                )
            )

    try:
        assert asyncio.run(table_names()) == {"alembic_version"}
    finally:
        asyncio.run(close_database(engine))

    assert migrate_module.main(["--database-url", database_url, "upgrade"]) == 0

    engine = create_database_engine(settings)

    async def upgraded_table_names() -> set[str]:
        async with engine.begin() as connection:
            return set(
                await connection.run_sync(
                    lambda sync_connection: sqlalchemy_inspect(
                        sync_connection
                    ).get_table_names()
                )
            )

    try:
        upgraded_tables = asyncio.run(upgraded_table_names())
    finally:
        asyncio.run(close_database(engine))

    assert "alembic_version" in upgraded_tables
    assert_identity_tables_present(upgraded_tables)


def test_runserver_delegates_default_arguments_to_uvicorn(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_load_environment(**kwargs: object) -> dict[str, str]:
        observed.update(kwargs)
        return {}

    def fake_run_uvicorn_command(args: list[str]) -> None:
        observed["uvicorn_args"] = args

    def fail_legacy_uvicorn_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("runserver should delegate to uvicorn's CLI command")

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(
        runserver_module, "run_uvicorn_command", fake_run_uvicorn_command, raising=False
    )
    monkeypatch.setattr(runserver_module.uvicorn, "run", fail_legacy_uvicorn_run)

    runserver_module.main([])

    assert observed["project_root"] == runtime_project_root()
    assert observed["uvicorn_args"] == [
        "app.asgi:app",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(DEFAULT_PORT),
    ]
    assert RELOAD_ENV_VAR_OPTION == "runserver_reload_env"
    assert APP_TARGET_OPTION == "runserver_app"


def test_runserver_loads_dotenv_from_runtime_project_root(monkeypatch) -> None:
    observed: dict[str, object] = {}

    class FakeEnv:
        def get(self, name: str, default: str | None = None) -> str | None:
            observed["reload_env_name"] = name
            return default

    def fake_load_environment(**kwargs: object) -> FakeEnv:
        observed.update(kwargs)
        return FakeEnv()

    def fake_run_uvicorn_command(args: list[str]) -> None:
        observed["uvicorn_args"] = args

    def fail_legacy_uvicorn_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("runserver should delegate to uvicorn's CLI command")

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(
        runserver_module, "run_uvicorn_command", fake_run_uvicorn_command, raising=False
    )
    monkeypatch.setattr(runserver_module.uvicorn, "run", fail_legacy_uvicorn_run)

    runserver_module.main([])

    assert observed["project_root"] == runtime_project_root()
    assert observed["reload_env_name"] == ENV_APP_RELOAD
    assert observed["uvicorn_args"] == [
        "app.asgi:app",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(DEFAULT_PORT),
    ]
    assert DEFAULT_RELOAD is False


def test_runserver_forwards_trailing_uvicorn_arguments(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_load_environment(**kwargs: object) -> dict[str, str]:
        observed.update(kwargs)
        return {ENV_APP_RELOAD: "on"}

    def fake_run_uvicorn_command(args: list[str]) -> None:
        observed["uvicorn_args"] = args

    def fail_legacy_uvicorn_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("runserver should delegate to uvicorn's CLI command")

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(
        runserver_module, "run_uvicorn_command", fake_run_uvicorn_command, raising=False
    )
    monkeypatch.setattr(runserver_module.uvicorn, "run", fail_legacy_uvicorn_run)

    runserver_module.main(
        [
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--",
            "--proxy-headers",
            "--forwarded-allow-ips",
            "10.0.0.10",
        ]
    )

    assert observed["uvicorn_args"] == [
        "app.asgi:app",
        "--host",
        "0.0.0.0",
        "--port",
        "9000",
        "--reload",
        "--proxy-headers",
        "--forwarded-allow-ips",
        "10.0.0.10",
    ]


def test_runserver_no_reload_overrides_reload_environment(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_load_environment(**kwargs: object) -> dict[str, str]:
        observed.update(kwargs)
        return {ENV_APP_RELOAD: "on"}

    def fake_run_uvicorn_command(args: list[str]) -> None:
        observed["uvicorn_args"] = args

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(
        runserver_module, "run_uvicorn_command", fake_run_uvicorn_command
    )

    runserver_module.main(["--no-reload"])

    assert observed["uvicorn_args"] == [
        "app.asgi:app",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(DEFAULT_PORT),
    ]


def test_runserver_rejects_extra_uvicorn_app_target(monkeypatch) -> None:
    monkeypatch.setattr(runserver_module, "load_environment", lambda **_: {})

    assert runserver_module.main(["--", "other.asgi:app"]) == 2
    assert runserver_module.main(["--", "--proxy-headers", "other.asgi:app"]) == 2


def test_runserver_allows_explicit_default_uvicorn_app_target() -> None:
    runserver_module._reject_extra_app_target(
        ["app.asgi:app"],
        app_target="app.asgi:app",
    )


@pytest.mark.parametrize(
    "option_value",
    [
        "/tmp/uvicorn.sock",
        "/tmp/uvicorn:socket",
        "127.0.0.1:9000",
    ],
)
def test_runserver_target_detection_does_not_reject_option_values(
    option_value: str,
) -> None:
    runserver_module._reject_extra_app_target(
        [option_value],
        app_target="app.asgi:app",
    )


def test_load_environment_reads_dotenv_without_mutating_process_environment(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv(ENV_APP_RELOAD, raising=False)
    (tmp_path / ".env").write_text("APP_RELOAD=true\n", encoding="utf-8")

    env = load_environment(environ={}, project_root=tmp_path)

    assert env.get(ENV_APP_RELOAD) == "true"
    assert ENV_APP_RELOAD not in os.environ


def test_load_environment_wraps_loader_failures_without_raw_detail(
    monkeypatch,
) -> None:
    def raise_sensitive_error(**_kwargs: object) -> None:
        raise RuntimeError("DATABASE_URL=postgresql://user:secret@example/app")

    monkeypatch.setattr(environment_module, "Env", raise_sensitive_error)

    with pytest.raises(
        ConfigurationError,
        match="Environment loader failed while initialising envex",
    ) as excinfo:
        load_environment(environ={}, read_dotenv=False)

    assert "RuntimeError" in str(excinfo.value)
    assert "secret" not in str(excinfo.value)
    assert "DATABASE_URL" not in str(excinfo.value)


def test_identity_env_settings_align_with_identity_option_fields() -> None:
    identity_option_enabled_fields = {
        identity_field.name
        for identity_field in fields(IdentityOptions)
        if identity_field.name.endswith("_enabled")
    }
    identity_env_enabled_fields = {
        env_setting.field_name
        for env_setting in IDENTITY_ENV_SETTINGS
        if env_setting.value_type == "bool"
        and env_setting.field_name.endswith("_enabled")
    }
    integration_enabled_fields = {
        f"{integration}_enabled" for integration in VALID_IDENTITY_INTEGRATIONS
    }

    assert identity_option_enabled_fields == identity_env_enabled_fields
    assert identity_option_enabled_fields == integration_enabled_fields


def test_create_app_mounts_configurable_static_files() -> None:
    settings = Settings(
        static_root=Path("src/test-static"),
        static_url_path="/assets/",
    )

    web_app = create_app(settings)

    static_routes = [r for r in web_app.routes if getattr(r, "name", None) == "static"]
    assert len(static_routes) == 1

    static_route = static_routes[0]
    assert static_route.path == "/assets"

    static_app = static_route.app
    assert isinstance(static_app, StaticFiles)
    assert Path(static_app.directory) == settings.static_root


def test_create_app_serves_static_files_from_configured_modules() -> None:
    web_app = create_app()

    static_routes = [r for r in web_app.routes if getattr(r, "name", None) == "static"]
    assert len(static_routes) == 1
    assert isinstance(static_routes[0].app, ComposedStaticFiles)

    response = TestClient(web_app).get("/static/styles/app.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert "--web-core-colour-page-bg" in response.text


def test_create_app_omitting_wevra_web_mounts_empty_static_route(
    tmp_path: Path,
) -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            project_root=tmp_path,
            app_config=build_test_app_config(tmp_path, modules=("app",)),
        )
    )

    try:
        static_routes = [
            route
            for route in web_app.routes
            if getattr(route, "name", None) == "static"
        ]
        response = TestClient(web_app).get("/static/styles/app.css")

        assert len(static_routes) == 1
        assert isinstance(static_routes[0].app, NoStaticFiles)
        assert str(web_app.url_path_for("static", path="/styles/app.css")) == (
            "/static/styles/app.css"
        )
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("text/plain")
        assert "--web-core-colour-page-bg" not in response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_create_app_applies_configured_route_prefixes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_root = tmp_path / "prefixed_route_app"
    package_root.mkdir()
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "routes.py").write_text(
        dedent(
            """
            from fastapi import APIRouter
            from fastapi.responses import Response

            router = APIRouter()

            @router.get("/ping", name="prefixed:ping")
            async def ping():
                return Response("prefixed")

            module_routers = {"default": router}
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            project_root=tmp_path,
            app_config=build_test_app_config(
                tmp_path,
                modules=("prefixed_route_app",),
                route_prefixes={"prefixed_route_app": {"default": "/tools"}},
            ),
        )
    )

    try:
        client = TestClient(web_app)

        assert client.get("/tools/ping").text == "prefixed"
        assert client.get("/ping").status_code == 404
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_settings_route_prefixes_preserve_default_labels_when_config_omits_module(
    tmp_path: Path,
) -> None:
    settings = Settings(
        database_url=SQLITE_MEMORY_DATABASE_URL,
        project_root=tmp_path,
        app_config=AppConfig(
            config_path=tmp_path / "app.toml",
            project_root=tmp_path,
            modules=("app", "wevra.auth"),
            routes=RouteOptions(prefixes={}),
            templates=TemplateOptions(auto_reload=True, cache_size=0),
            static=StaticOptions(
                url_path="/static/",
                export_root=Path("static"),
            ),
        ),
    )

    assert settings.route_prefixes == {
        "app": {"default": ""},
        "wevra.auth": {"account": "/account", "api": ""},
    }


def test_create_app_registers_routes_only_from_configured_modules(
    tmp_path: Path,
) -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            project_root=tmp_path,
            app_config=build_test_app_config(tmp_path, modules=("app",)),
        )
    )

    try:
        route_names = {
            route.name
            for route in web_app.routes
            if isinstance(route, APIRoute) and route.name is not None
        }

        assert "public:home" in route_names
        assert "auth:login" not in route_names
        assert "health" in route_names
        assert not hasattr(web_app.state, "identity_options")
        assert not hasattr(web_app.state, "identity_delivery")
        assert not hasattr(web_app.state, "fastapi_users")
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_create_app_honours_explicit_template_root_with_module_templates(
    tmp_path: Path,
) -> None:
    template_root = tmp_path / "templates"
    (template_root / "public/pages").mkdir(parents=True)
    (template_root / "public/pages/home.html").write_text(
        "filesystem template override",
        encoding="utf-8",
    )
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            project_root=tmp_path,
            template_root=template_root,
            app_config=build_test_app_config(
                tmp_path,
                modules=("app", "wevra.web"),
            ),
        )
    )

    try:
        response = TestClient(web_app).get("/")

        assert response.status_code == 200
        assert response.text == "filesystem template override"
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_missing_static_asset_does_not_render_html_error_page() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/static/missing.css")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/plain")
    assert "<!doctype html>" not in response.text.lower()
    assert response.text == "Not Found"


def test_create_app_applies_default_cross_origin_opener_policy() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))

    try:
        response = TestClient(web_app).get("/")

        assert response.headers[COOP_HEADER_NAME] == "same-origin"
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_create_app_can_disable_cross_origin_opener_policy() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            cross_origin_opener_policy=None,
        )
    )

    try:
        response = TestClient(web_app).get("/")

        assert COOP_HEADER_NAME not in response.headers
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_settings_default_resource_roots_are_not_filesystem_overrides(
    tmp_path: Path,
) -> None:
    settings = Settings(project_root=tmp_path)

    assert settings.app_config is None
    assert settings.modules == ("app", "wevra.web", "wevra.auth")
    assert settings.database_url == (
        f"sqlite+aiosqlite:///{(tmp_path / 'app.sqlite3').resolve().as_posix()}"
    )
    assert settings.template_auto_reload is None
    assert settings.template_cache_size == 400
    assert settings.template_root is None
    assert settings.static_root is None
    assert settings.migrations_root is None
    assert settings.uses_filesystem_template_root is False
    assert settings.uses_filesystem_static_root is False
    assert settings.alembic_config == (tmp_path / "alembic.ini").resolve()


def test_settings_resolves_explicit_resource_roots_from_project_root(
    tmp_path: Path,
) -> None:
    settings = Settings(
        project_root=tmp_path,
        template_root="templates",
        static_root="assets",
        migrations_root="database/migrations",
    )

    assert settings.template_root == (tmp_path / "templates").resolve()
    assert settings.static_root == (tmp_path / "assets").resolve()
    assert settings.migrations_root == (tmp_path / "database/migrations").resolve()
    assert settings.uses_filesystem_template_root is True
    assert settings.uses_filesystem_static_root is True


@pytest.mark.parametrize(
    "setting_name",
    ("template_root", "static_root", "migrations_root", "alembic_config"),
)
def test_settings_rejects_blank_path_values(setting_name: str) -> None:
    with pytest.raises(
        ConfigurationError,
        match=rf"{setting_name} must not be blank\.",
    ):
        Settings(**{setting_name: "   "})


def test_settings_default_database_url_uses_async_sqlalchemy_driver() -> None:
    assert Settings().database_url.endswith("/app.sqlite3")
    assert Settings().database_url != SQLITE_MEMORY_DATABASE_URL
    assert is_supported_database_url(Settings().database_url)
    assert is_supported_database_url("postgresql+asyncpg://user:pass@db/app")
    assert is_supported_database_url(SQLITE_MEMORY_DATABASE_URL)
    assert not is_supported_database_url("sqlite://:memory:")


def test_settings_resolves_sqlite_database_url_without_moving_query_into_path(
    tmp_path,
) -> None:
    settings = Settings(
        project_root=tmp_path,
        database_url="sqlite+aiosqlite:///app.sqlite3?mode=ro#fragment",
    )

    assert settings.database_url == (
        f"sqlite+aiosqlite:///"
        f"{(tmp_path / 'app.sqlite3').resolve().as_posix()}?mode=ro#fragment"
    )


def test_load_settings_rejects_missing_default_app_toml(tmp_path) -> None:
    with pytest.raises(
        ConfigurationError,
        match="Application config file could not be resolved",
    ):
        load_settings(environ={}, project_root=tmp_path, read_dotenv=False)


def test_load_settings_reads_default_app_toml(tmp_path) -> None:
    config_path = write_app_config(
        tmp_path / "app.toml",
        modules=("app", "wevra.auth"),
        static_url_path="/assets/",
        database_url="sqlite+aiosqlite:///identity.sqlite3",
    )

    settings = load_settings(environ={}, project_root=tmp_path, read_dotenv=False)

    assert settings.app_config is not None
    assert settings.app_config.config_path == config_path.resolve()
    assert settings.app_config.database_url == "sqlite+aiosqlite:///identity.sqlite3"
    assert settings.modules == ("app", "wevra.auth")
    assert settings.template_auto_reload is True
    assert settings.template_cache_size == 0
    assert settings.template_root is None
    assert settings.static_root is None
    assert settings.static_mount_path == "/assets"
    assert settings.database_url == sqlite_file_url(tmp_path / "identity.sqlite3")
    assert settings.identity_options.password_minimum_length == 12
    assert settings.identity_options.password_common_fragments == (
        "admin",
        "password",
        "test",
    )
    assert settings.identity_options.token_secrets_configured is False


def test_load_settings_database_url_overrides_app_config_database_url(
    tmp_path: Path,
) -> None:
    write_app_config(
        tmp_path / "app.toml",
        database_url="sqlite+aiosqlite:///from-config.sqlite3",
    )

    settings = load_settings(
        environ={ENV_DATABASE_URL: "sqlite+aiosqlite:///from-env.sqlite3"},
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.database_url == sqlite_file_url(tmp_path / "from-env.sqlite3")


def test_load_settings_identity_env_preserves_app_auth_config(
    tmp_path: Path,
) -> None:
    write_app_config(
        tmp_path / "app.toml",
        auth_options={
            "reset_password_token_secret": "configured-reset-secret",
            "verification_token_secret": "configured-verification-secret",
        },
    )

    settings = load_settings(
        environ={ENV_SESSION_LIFETIME: "3600"},
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.identity_options.session_lifetime_seconds == 3600
    assert settings.identity_options.password_minimum_length == 12
    assert settings.identity_options.password_common_fragments == (
        "admin",
        "password",
        "test",
    )
    assert settings.identity_options.reset_password_token_secret == (
        "configured-reset-secret"
    )
    assert settings.identity_options.verification_token_secret == (
        "configured-verification-secret"
    )
    assert settings.identity_options.token_secrets_configured is True


def test_load_settings_ignores_removed_auth_database_url_env(
    tmp_path: Path,
) -> None:
    write_app_config(
        tmp_path / "app.toml",
        database_url="sqlite+aiosqlite:///from-config.sqlite3",
    )

    settings = load_settings(
        environ={"AUTH_DATABASE_URL": "sqlite+aiosqlite:///ignored.sqlite3"},
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.database_url == sqlite_file_url(tmp_path / "from-config.sqlite3")


def test_load_settings_uses_app_config_environment_override(tmp_path) -> None:
    config_path = write_app_config(
        tmp_path / "config" / "application.toml",
        modules=("app",),
        static_url_path="/public-static/",
    )

    settings = load_settings(
        environ={ENV_APP_CONFIG: "config/application.toml"},
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.app_config is not None
    assert settings.app_config.config_path == config_path.resolve()
    assert settings.modules == ("app",)
    assert settings.template_root is None
    assert settings.static_root is None
    assert settings.static_mount_path == "/public-static"


def test_load_settings_environment_overrides_app_toml_paths(tmp_path) -> None:
    write_app_config(
        tmp_path / "app.toml",
        static_url_path="/configured-static/",
    )

    settings = load_settings(
        environ={
            ENV_STATIC_ROOT: "env/static",
            ENV_STATIC_URL: "assets",
            ENV_TEMPLATE_ROOT: "env/templates",
        },
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.app_config is not None
    assert settings.template_root == (tmp_path / "env/templates").resolve()
    assert settings.static_root == (tmp_path / "env/static").resolve()
    assert settings.static_mount_path == "/assets"


def test_load_settings_rejects_missing_app_config_override(tmp_path) -> None:
    with pytest.raises(ConfigurationError, match="App config file does not exist"):
        load_settings(
            environ={ENV_APP_CONFIG: "missing.toml"},
            project_root=tmp_path,
            read_dotenv=False,
        )


def test_load_settings_uses_environment_values(tmp_path) -> None:
    write_app_config(tmp_path / "app.toml")
    database_url = "postgresql+asyncpg://user:password@db.example/app"
    enabled_value = "true"
    settings = load_settings(
        environ={
            ENV_APP_NAME: "env-app",
            ENV_APP_ENV: "production",
            ENV_DATABASE_URL: database_url,
            ENV_CSRF_SECRET: "csrf-secret",
            ENV_CSRF_SECURE: "true",
            ENV_RESET_SECRET: "reset-secret",
            ENV_VERIFICATION_SECRET: "verification-secret",
            ENV_SESSION_COOKIE: "session-id",
            ENV_SESSION_FORCE_SECURE: "true",
            ENV_SESSION_LIFETIME: "3600",
            identity_env_setting_name(PROVIDER): enabled_value,
            identity_env_setting_name(TOTP): enabled_value,
            identity_env_setting_name(PASSKEY): enabled_value,
            ENV_STATIC_URL: "assets",
        },
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.app_name == "env-app"
    assert settings.deployment_environment == "production"
    assert settings.database_url == database_url
    assert settings.csrf_token_secret == "csrf-secret"
    assert settings.csrf_cookie_secure is True
    assert settings.identity_options.session_cookie_name == "session-id"
    assert settings.identity_options.session_cookie_force_secure is True
    assert settings.identity_options.session_lifetime_seconds == 3600
    assert settings.identity_options.reset_password_token_secret == "reset-secret"
    assert settings.identity_options.verification_token_secret == "verification-secret"
    assert settings.identity_options.provider_enabled is True
    assert settings.identity_options.totp_enabled is True
    assert settings.identity_options.passkey_enabled is True
    assert settings.static_mount_path == "/assets"


def test_load_settings_reads_local_dotenv(tmp_path) -> None:
    write_app_config(tmp_path / "app.toml")
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "APP_NAME=dotenv-app",
                "DATABASE_URL=sqlite+aiosqlite:///dotenv.sqlite3",
                "SESSION_LIFETIME=120",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_settings(environ={}, project_root=tmp_path)

    assert settings.app_name == "dotenv-app"
    assert settings.database_url == (
        f"sqlite+aiosqlite:///{(tmp_path / 'dotenv.sqlite3').resolve().as_posix()}"
    )
    assert settings.identity_options.session_lifetime_seconds == 120


def test_load_settings_resolves_env_paths_from_project_root(tmp_path) -> None:
    write_app_config(tmp_path / "app.toml")
    settings = load_settings(
        environ={
            ENV_ALEMBIC_CONFIG: "config/alembic.ini",
            ENV_MIGRATIONS_ROOT: "database/migrations",
            ENV_STATIC_ROOT: "assets",
            ENV_TEMPLATE_ROOT: "templates",
        },
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.alembic_config == (tmp_path / "config/alembic.ini").resolve()
    assert settings.migrations_root == (tmp_path / "database/migrations").resolve()
    assert settings.static_root == (tmp_path / "assets").resolve()
    assert settings.template_root == (tmp_path / "templates").resolve()


@pytest.mark.parametrize(
    ("env_name", "expected_message"),
    [
        (ENV_DATABASE_URL, "DATABASE_URL must not be blank"),
        (ENV_APP_CONFIG, "APP_CONFIG must not be blank"),
        (ENV_SESSION_LIFETIME, "SESSION_LIFETIME must not be blank"),
        (ENV_STATIC_URL, "STATIC_URL must not be blank"),
        (ENV_TEMPLATE_ROOT, "TEMPLATE_ROOT must not be blank"),
    ],
)
def test_load_settings_rejects_blank_env_values(
    tmp_path,
    env_name: str,
    expected_message: str,
) -> None:
    if env_name != ENV_APP_CONFIG:
        write_app_config(tmp_path / "app.toml")
    with pytest.raises(ConfigurationError, match=expected_message):
        load_settings(
            environ={env_name: ""},
            project_root=tmp_path,
            read_dotenv=False,
        )


def test_explicit_settings_ignore_environment_values(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(ENV_APP_NAME, "env-app")
    monkeypatch.setenv(ENV_DATABASE_URL, "sqlite+aiosqlite:///env.sqlite3")

    settings = Settings(
        app_name="explicit-app",
        database_url="sqlite+aiosqlite:///explicit.sqlite3",
        project_root=tmp_path,
    )

    assert settings.app_name == "explicit-app"
    assert settings.database_url == (
        f"sqlite+aiosqlite:///{(tmp_path / 'explicit.sqlite3').resolve().as_posix()}"
    )


def test_sqlite_database_path_ignores_url_query_and_fragment() -> None:
    assert sqlite_database_path("sqlite+aiosqlite:///app.sqlite3?mode=ro") == (
        Path("app.sqlite3")
    )
    assert sqlite_database_path("sqlite+aiosqlite:///app.sqlite3#fragment") == Path(
        "app.sqlite3"
    )


def test_settings_include_identity_options() -> None:
    settings = Settings()
    options = settings.identity_options

    assert settings.csrf_token_secret
    assert settings.csrf_cookie_secure is False
    assert settings.csrf_token_secret_configured is False
    assert options.account_creation_policy == "admin-created"
    assert options.session_cookie_name == "uniquode_session"
    assert options.session_cookie_force_secure is False
    assert options.session_lifetime_seconds == 2_592_000
    assert options.password_minimum_length == 12
    assert options.password_minimum_strength == 0.45
    assert options.password_minimum_character_categories == 2
    assert options.token_secrets_configured is False
    assert_identity_integration_flags(
        options=options,
        integration_flags=DEFAULT_IDENTITY_INTEGRATION_FLAGS,
    )


def test_settings_default_identity_session_cookie_name_is_app_specific() -> None:
    settings = Settings()

    assert IdentityOptions().session_cookie_name == WEVRA_DEFAULT_SESSION_COOKIE_NAME
    assert settings.identity_options.session_cookie_name == "uniquode_session"
    assert (
        settings.identity_options.session_cookie_name
        != WEVRA_DEFAULT_SESSION_COOKIE_NAME
    )


def test_settings_preserves_explicit_identity_session_cookie_name() -> None:
    settings = Settings(
        identity_options=IdentityOptions(session_cookie_name="custom_session"),
    )

    assert settings.identity_options.session_cookie_name == "custom_session"


def test_load_settings_uses_app_identity_session_cookie_default_with_identity_env(
    tmp_path,
) -> None:
    write_app_config(tmp_path / "app.toml")
    settings = load_settings(
        environ={ENV_SESSION_LIFETIME: "3600"},
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.identity_options.session_lifetime_seconds == 3600
    assert settings.identity_options.session_cookie_name == "uniquode_session"
    assert (
        settings.identity_options.session_cookie_name
        != WEVRA_DEFAULT_SESSION_COOKIE_NAME
    )


def test_identity_options_accept_public_signup_policy() -> None:
    options = IdentityOptions(account_creation_policy="public-signup")

    assert options.account_creation_policy == "public-signup"


def test_identity_options_reject_invalid_account_creation_policy() -> None:
    with pytest.raises(ConfigurationError, match="Account creation policy"):
        IdentityOptions(account_creation_policy="public_signup")  # type: ignore[arg-type]


def test_load_settings_reads_account_creation_policy_env(tmp_path) -> None:
    write_app_config(tmp_path / "app.toml")
    settings = load_settings(
        environ={ENV_ACCOUNT_CREATION_POLICY: "public-signup"},
        project_root=tmp_path,
        read_dotenv=False,
    )

    assert settings.identity_options.account_creation_policy == "public-signup"


def test_identity_options_generate_local_token_secrets() -> None:
    first = IdentityOptions()
    second = IdentityOptions()

    assert first.reset_password_token_secret
    assert first.verification_token_secret
    assert first.reset_password_token_secret != second.reset_password_token_secret
    assert first.verification_token_secret != second.verification_token_secret


def test_settings_logs_generated_local_csrf_token_secret(caplog) -> None:
    caplog.set_level(logging.INFO, logger="app.settings")

    settings = Settings()

    assert settings.csrf_token_secret_configured is False
    assert "Generated startup-local CSRF token secret." in caplog.text


def test_identity_options_reject_invalid_session_lifetime() -> None:
    with pytest.raises(
        ConfigurationError,
        match="Session lifetime must be a positive number of seconds",
    ):
        IdentityOptions(session_lifetime_seconds=0)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"password_minimum_length": 0}, "Password minimum length"),
        ({"password_minimum_strength": -0.1}, "Password minimum strength"),
        ({"password_minimum_strength": 1.1}, "Password minimum strength"),
        (
            {"password_minimum_character_categories": 0},
            "Password minimum character categories",
        ),
    ],
)
def test_identity_options_reject_invalid_password_policy_settings(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        IdentityOptions(**kwargs)


def test_identity_options_reject_blank_token_secrets() -> None:
    with pytest.raises(
        ConfigurationError, match="Reset password token secret must not be blank"
    ):
        IdentityOptions(
            reset_password_token_secret="",
            verification_token_secret="verification-secret",
        )

    with pytest.raises(
        ConfigurationError, match="Verification token secret must not be blank"
    ):
        IdentityOptions(
            reset_password_token_secret="reset-secret",
            verification_token_secret="   ",
        )


def test_non_local_settings_require_configured_identity_token_secrets() -> None:
    with pytest.raises(
        ConfigurationError,
        match="Non-local deployments must configure identity reset",
    ):
        Settings(deployment_environment="production")

    settings = Settings(
        deployment_environment="production",
        csrf_token_secret="production-csrf-secret",
        identity_options=IdentityOptions(
            reset_password_token_secret="production-reset-secret",
            verification_token_secret="production-verification-secret",
            session_cookie_force_secure=True,
        ),
    )

    assert settings.identity_options.token_secrets_configured is True
    assert settings.csrf_token_secret_configured is True
    assert settings.csrf_cookie_secure is True


def test_non_local_settings_skip_identity_policy_when_wevra_auth_is_omitted(
    tmp_path: Path,
) -> None:
    settings = Settings(
        deployment_environment="production",
        csrf_token_secret="production-csrf-secret",
        app_config=build_test_app_config(
            tmp_path,
            modules=("app", "wevra.web"),
        ),
    )

    assert settings.identity_enabled is False
    assert settings.modules == ("app", "wevra.web")
    assert settings.csrf_cookie_secure is True


def test_non_local_settings_require_secure_session_cookies() -> None:
    identity_options = IdentityOptions(
        session_cookie_force_secure=False,
        reset_password_token_secret="production-reset-secret",
        verification_token_secret="production-verification-secret",
    )

    with pytest.raises(
        ConfigurationError,
        match="auth.session_cookie_force_secure = true",
    ):
        Settings(
            deployment_environment="production",
            csrf_token_secret="production-csrf-secret",
            identity_options=identity_options,
        )


@pytest.mark.parametrize(
    ("scheme", "expected_secure"),
    [
        ("http", False),
        ("https", True),
        (None, False),
        ("ws", False),
        ("wss", True),
        ("custom", False),
    ],
)
def test_session_cookie_security_derives_from_request_scheme(
    scheme: object,
    expected_secure: bool,
) -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/account",
            "scheme": scheme,
            "headers": [],
        }
    )

    assert session_cookie_secure_for_request(request) is expected_secure


def test_session_cookie_security_can_be_forced_for_untrusted_scheme() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/account",
            "scheme": "http",
            "headers": [],
        }
    )

    assert session_cookie_secure_for_request(request, force_secure=True) is True


def test_session_cookie_security_warns_once_for_forwarded_https_on_http_scheme(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(identity_users, "_logged_forward_header_misconfig", False)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/account",
            "scheme": "http",
            "headers": [(b"x-forwarded-proto", b"https")],
        }
    )

    with caplog.at_level(logging.WARNING, logger="wevra.auth.sessions"):
        assert session_cookie_secure_for_request(request) is False
        assert session_cookie_secure_for_request(request) is False

    warnings = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING
        and "ASGI request scheme is 'http'" in record.message
    ]
    assert len(warnings) == 1
    assert "ASGI request scheme is 'http'" in caplog.text
    assert "session_cookie_force_secure" in caplog.text


@pytest.mark.parametrize(
    ("forwarded_header", "expected"),
    [
        ("for=192.0.2.43;proto=https;by=203.0.113.43", True),
        ('for=192.0.2.43; proto="https"', True),
        ("for=192.0.2.43;proto=http, for=198.51.100.17;proto=https", True),
        ("for=192.0.2.43;host=proto=https.example", False),
        ("for=192.0.2.43;xproto=https", False),
        ("for=192.0.2.43;proto=httpsx", False),
    ],
)
def test_session_cookie_security_parses_forwarded_proto_parameter(
    forwarded_header: str,
    expected: bool,
) -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/account",
            "scheme": "http",
            "headers": [(b"forwarded", forwarded_header.encode())],
        }
    )

    assert identity_users._has_secure_forwarded_proto(request) is expected


def test_non_local_settings_require_configured_csrf_token_secret() -> None:
    identity_options = IdentityOptions(
        reset_password_token_secret="production-reset-secret",
        verification_token_secret="production-verification-secret",
        session_cookie_force_secure=True,
    )

    with pytest.raises(
        ConfigurationError,
        match="Non-local deployments must configure a stable CSRF token secret",
    ):
        Settings(
            deployment_environment="production",
            identity_options=identity_options,
        )

    with pytest.raises(ConfigurationError, match="CSRF token secret must not be blank"):
        Settings(
            deployment_environment="production",
            csrf_token_secret="   ",
            identity_options=identity_options,
        )

    with pytest.raises(
        ConfigurationError,
        match="Non-local deployments must use secure CSRF cookies",
    ):
        Settings(
            deployment_environment="production",
            csrf_token_secret="production-csrf-secret",
            csrf_cookie_secure=False,
            identity_options=identity_options,
        )


def test_identity_options_expose_integration_flags() -> None:
    enabled_flags = {name: True for name in DEFAULT_IDENTITY_INTEGRATION_FLAGS}
    options = IdentityOptions(
        provider_enabled=True,
        totp_enabled=True,
        passkey_enabled=True,
    )

    assert_identity_integration_flags(
        options=options,
        integration_flags=enabled_flags,
    )


def test_create_app_configures_database_and_identity_boundaries() -> None:
    web_app = create_app()

    try:
        assert isinstance(web_app.state.database, Database)
        assert isinstance(web_app.state.fastapi_users, FastAPIUsers)
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_create_app_without_explicit_settings_uses_environment(
    tmp_path,
    monkeypatch,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'app.sqlite3').as_posix()}"
    monkeypatch.setenv(ENV_APP_NAME, "environment-app")
    monkeypatch.setenv(ENV_DATABASE_URL, database_url)

    web_app = create_app()

    try:
        assert web_app.title == "environment-app"
        assert web_app.state.settings.database_url == database_url
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_create_database_engine_uses_configured_url() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    engine = create_database_engine(settings)

    try:
        assert isinstance(engine, AsyncEngine)
        assert str(engine.url) == settings.database_url
    finally:
        asyncio.run(close_database(engine))


def test_create_database_builds_async_session_factory() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    database = create_database(settings)

    try:
        assert isinstance(database.engine, AsyncEngine)
        assert isinstance(database.session_factory, async_sessionmaker)
    finally:
        asyncio.run(close_database(database))


def test_session_scope_yields_async_session() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    async def assert_session() -> None:
        async with session_scope(session_factory) as session:
            assert isinstance(session, AsyncSession)
            result = await session.execute(text("select 1"))
            assert result.scalar_one() == 1

    try:
        asyncio.run(assert_session())
    finally:
        asyncio.run(close_database(engine))


def test_identity_models_define_fastapi_users_columns() -> None:
    user_columns = set(User.__table__.columns.keys())
    provider_columns = set(IdentityProvider.__table__.columns.keys())
    external_identity_link_columns = set(ExternalIdentityLink.__table__.columns.keys())
    access_token_columns = set(AccessToken.__table__.columns.keys())

    assert {
        "id",
        "email",
        "hashed_password",
        "is_active",
        "is_superuser",
        "is_verified",
    }.issubset(user_columns)
    assert {
        "id",
        "provider_name",
        "provider_subject",
        "access_token",
        "account_email",
        "provider_enabled",
        "provider_metadata",
    }.issubset(provider_columns)
    assert {
        "user_id",
        "provider_id",
    }.issubset(external_identity_link_columns)
    assert {"token", "created_at", "user_id"}.issubset(access_token_columns)
    assert User.__tablename__ == "identity_user"
    assert IdentityProvider.__tablename__ == "identity_provider"
    assert AccessToken.__tablename__ == "identity_access_token"
    assert ExternalIdentityLink.__tablename__ == "identity_external_identity_link"


def test_external_identity_models_link_to_local_user_and_provider() -> None:
    external_link_foreign_keys = ExternalIdentityLink.__table__.columns[
        "user_id"
    ].foreign_keys
    external_provider_foreign_keys = ExternalIdentityLink.__table__.columns[
        "provider_id"
    ].foreign_keys
    access_token_foreign_keys = AccessToken.__table__.columns["user_id"].foreign_keys

    assert {str(foreign_key.column) for foreign_key in external_link_foreign_keys} == {
        "identity_user.id"
    }
    assert {
        str(foreign_key.column) for foreign_key in external_provider_foreign_keys
    } == {"identity_provider.id"}
    assert {str(foreign_key.column) for foreign_key in access_token_foreign_keys} == {
        "identity_user.id"
    }
    assert User.external_identity_links.property.mapper.class_ is ExternalIdentityLink


def test_sqlalchemy_metadata_creates_identity_tables() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    engine = create_database_engine(settings)

    async def assert_tables() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            table_names = await connection.run_sync(
                lambda sync_connection: sqlalchemy_inspect(
                    sync_connection
                ).get_table_names()
            )

        assert_identity_tables_present(set(table_names))

    try:
        asyncio.run(assert_tables())
    finally:
        asyncio.run(close_database(engine))


def test_wevra_auth_models_export_migration_metadata() -> None:
    assert wevra_auth_metadata is Base.metadata


def test_model_packages_are_derived_from_modules() -> None:
    assert model_packages_from_modules(("app", "wevra.auth")) == ("wevra.auth.models",)


def test_configured_model_packages_load_migration_metadata_in_order() -> None:
    metadata_values = load_model_metadata(project_root=runtime_project_root())

    assert len(metadata_values) == 1
    assert all(isinstance(value, MetaData) for value in metadata_values)
    assert metadata_values == (wevra_auth_metadata,)


def test_model_metadata_loader_deduplicates_shared_metadata_objects() -> None:
    metadata_values = load_model_metadata(("wevra.db.models", "wevra.auth.models"))

    assert metadata_values == (wevra_auth_metadata,)


def test_model_metadata_loader_reads_modules_from_app_toml(
    tmp_path,
) -> None:
    write_app_config(
        tmp_path / "app.toml",
        modules=("wevra.auth", "app"),
    )

    metadata_values = load_model_metadata(project_root=tmp_path)

    assert metadata_values == (wevra_auth_metadata,)


def test_model_metadata_loader_uses_default_modules_when_app_toml_is_absent(
    tmp_path,
) -> None:
    metadata_values = load_model_metadata(
        project_root=tmp_path,
        default_modules=("app", "wevra.web", "wevra.auth"),
    )

    assert metadata_values == (wevra_auth_metadata,)


def test_model_metadata_loader_preserves_composition_error_cause(
    tmp_path,
) -> None:
    with pytest.raises(
        MigrationConfigError,
        match="App config file does not exist",
    ) as exc_info:
        load_model_metadata(project_root=tmp_path)

    assert isinstance(exc_info.value.__cause__, CompositionError)


def test_model_metadata_loader_skips_modules_without_models() -> None:
    assert load_model_metadata(modules=("app",)) == ()


def test_model_metadata_loader_reports_missing_module() -> None:
    with pytest.raises(
        MigrationConfigError,
        match="Configured module 'missing_module'",
    ) as exc_info:
        load_model_metadata(modules=("missing_module",))

    assert isinstance(exc_info.value.__cause__, DataCompositionError)


def test_model_metadata_loader_rejects_invalid_installed_module_models(
    tmp_path,
    monkeypatch,
) -> None:
    module_root = tmp_path / "invalid_models_app"
    module_root.mkdir()
    (module_root / "__init__.py").write_text("", encoding="utf-8")
    (module_root / "models.py").write_text("metadata = object()\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    with pytest.raises(
        MigrationConfigError,
        match=r"invalid_models_app.models.*must expose SQLAlchemy metadata",
    ) as exc_info:
        load_model_metadata(modules=("invalid_models_app",))

    assert isinstance(exc_info.value.__cause__, DataCompositionError)


def test_alembic_metadata_loading_avoids_runtime_startup_imports() -> None:
    code = """
import json
import sys
from pathlib import Path

from wevra.db.migration_metadata import load_model_metadata
from wevra.tools.project import runtime_project_root

metadata_values = load_model_metadata(project_root=runtime_project_root())
forbidden_modules = (
    "wevra.auth.sessions",
    "jinja2",
    "app.app",
    "app.asgi",
    "app.routes",
    "wevra.web.rendering",
)
print(
    json.dumps(
        {
            "metadata_count": len(metadata_values),
            "forbidden_imports": [
                module for module in forbidden_modules if module in sys.modules
            ],
        }
    )
)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload == {"metadata_count": 1, "forbidden_imports": []}


def test_migrate_alembic_config_carries_app_config_path(tmp_path) -> None:
    config_path = write_app_config(tmp_path / "app.toml")

    settings = load_settings(environ={}, project_root=tmp_path, read_dotenv=False)
    config = migrate_module.build_alembic_config(settings)

    assert config.get_main_option("app_config") == config_path.resolve().as_posix()
    assert config.get_main_option("script_location") == "wevra.db:migrations"
    assert config.get_main_option("version_locations").endswith(
        "wevra/auth/migrations/versions"
    )


def test_model_metadata_loader_with_no_packages_returns_empty_tuple() -> None:
    assert load_model_metadata(()) == ()


def test_model_metadata_loader_rejects_packages_without_metadata() -> None:
    with pytest.raises(
        MigrationConfigError,
        match=r"dummy_no_metadata.*Module origin:.*Available attributes:",
    ) as exc_info:
        load_model_metadata(("dummy_no_metadata",))

    assert isinstance(exc_info.value.__cause__, DataCompositionError)


def test_model_metadata_loader_rejects_non_metadata_attribute() -> None:
    with pytest.raises(
        MigrationConfigError,
        match=r"dummy_invalid_metadata.*Module origin:.*Available attributes:",
    ) as exc_info:
        load_model_metadata(("dummy_invalid_metadata",))

    assert isinstance(exc_info.value.__cause__, DataCompositionError)


def test_model_metadata_loader_reports_missing_configured_package() -> None:
    with pytest.raises(MigrationConfigError, match="could not be imported") as exc_info:
        load_model_metadata(("missing_model_package",))

    assert isinstance(exc_info.value.__cause__, DataCompositionError)


def test_model_metadata_loader_preserves_nested_import_failures() -> None:
    with pytest.raises(ModuleNotFoundError, match="missing_dependency"):
        load_model_metadata(("dummy_missing_dependency",))


def test_identity_authentication_backend_uses_http_only_session_cookie() -> None:
    options = IdentityOptions(
        session_cookie_name="u_test_session",
        session_cookie_force_secure=True,
        session_lifetime_seconds=3600,
    )

    backend = create_authentication_backend(options)

    assert isinstance(backend, AuthenticationBackend)
    assert backend.name == "session"
    assert isinstance(backend.transport, CookieTransport)
    assert backend.transport.cookie_name == "u_test_session"
    assert backend.transport.cookie_max_age == 3600
    assert backend.transport.cookie_secure is True
    assert backend.transport.cookie_httponly is True


def test_identity_authentication_backend_allows_http_development_cookie() -> None:
    backend = create_authentication_backend(IdentityOptions())

    assert isinstance(backend.transport, CookieTransport)
    assert backend.transport.cookie_secure is False


def test_user_manager_creates_and_authenticates_user() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    async def assert_user_flow() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(session_factory) as session:
            manager = create_user_manager(session, settings.identity_options)
            created_user = await manager.create(
                UserCreate(email="person@example.com", password="correct horse"),
                safe=True,
            )

            assert created_user.email == "person@example.com"
            assert created_user.hashed_password != "correct horse"

            credentials = OAuth2PasswordRequestForm(
                username="person@example.com",
                password="correct horse",
            )
            authenticated_user = await manager.authenticate(credentials)

            assert authenticated_user is not None
            assert authenticated_user.id == created_user.id

    try:
        asyncio.run(assert_user_flow())
    finally:
        asyncio.run(close_database(engine))


def test_database_strategy_persists_and_destroys_session_token() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    async def assert_strategy_flow() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(session_factory) as session:
            manager = create_user_manager(session, settings.identity_options)
            user = await manager.create(
                UserCreate(email="session@example.com", password="correct horse"),
                safe=True,
            )
            strategy = create_database_strategy(session, settings.identity_options)

            token = await strategy.write_token(user)
            assert token

            token_user = await strategy.read_token(token, manager)
            assert token_user is not None
            assert token_user.id == user.id

            await strategy.destroy_token(token, user)
            assert await strategy.read_token(token, manager) is None

    try:
        asyncio.run(assert_strategy_flow())
    finally:
        asyncio.run(close_database(engine))


def test_user_manager_rejects_blank_passwords() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    async def assert_password_validation() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(session_factory) as session:
            manager = create_user_manager(session, settings.identity_options)
            with pytest.raises(InvalidPasswordException):
                await manager.create(
                    UserCreate(email="blank-password@example.com", password="   "),
                    safe=True,
                )

            users = (await session.execute(select(User))).scalars().all()
            assert users == []

    try:
        asyncio.run(assert_password_validation())
    finally:
        asyncio.run(close_database(engine))


def test_user_manager_uses_configured_password_policy() -> None:
    class RejectingPasswordPolicy:
        def strength(
            self,
            password: str,
            user: object | None = None,
        ) -> PasswordStrength:
            del password, user
            return PasswordStrength(
                score=0.0,
                label="weak",
                feedback=("Rejected by custom policy.",),
            )

        def validate(
            self,
            password: str,
            user: object | None = None,
        ) -> Result[str]:
            del password, user
            return Result.failure(
                ERROR_PASSWORD_TOO_WEAK,
                "Rejected by custom policy.",
            )

    settings = Settings(
        database_url=SQLITE_MEMORY_DATABASE_URL,
        identity_options=IdentityOptions(password_policy=RejectingPasswordPolicy()),
    )
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    async def assert_policy_enforcement() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(session_factory) as session:
            manager = create_user_manager(session, settings.identity_options)
            with pytest.raises(InvalidPasswordException) as exc_info:
                await manager.create(
                    UserCreate(email="rejected-password@example.com", password="valid"),
                    safe=True,
                )

            assert exc_info.value.reason == (
                "Password does not meet the strength requirement."
            )
            users = (await session.execute(select(User))).scalars().all()
            assert users == []

    try:
        asyncio.run(assert_policy_enforcement())
    finally:
        asyncio.run(close_database(engine))


def test_authentication_ceremony_finalisation_creates_active_user_session() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    async def assert_finalisation() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(web_app.state.database.session_factory) as session:
            manager = create_user_manager(
                session, web_app.state.settings.identity_options
            )
            user = await manager.create(
                UserCreate(email="ceremony@example.com", password="correct horse"),
                safe=True,
            )

        request = Request({"type": "http", "app": web_app})
        result = await identity_users.complete_authentication_ceremony(request, user)

        assert result.is_ok() is True
        assert result.value

        session_request = app_request_with_session_cookie(
            web_app,
            session_cookie_name=web_app.state.settings.identity_options.session_cookie_name,
            session_token=result.value,
        )
        resolved_user = await identity_users.resolve_current_user(session_request)
        assert resolved_user is not None
        assert resolved_user.email == "ceremony@example.com"

    try:
        asyncio.run(assert_finalisation())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_authentication_ceremony_finalisation_rejects_inactive_user() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    async def assert_finalisation() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(web_app.state.database.session_factory) as session:
            manager = create_user_manager(
                session, web_app.state.settings.identity_options
            )
            user = await manager.create(
                UserCreate(
                    email="inactive-ceremony@example.com",
                    password="correct horse",
                    is_active=False,
                ),
                safe=False,
            )

        request = Request({"type": "http", "app": web_app})
        result = await identity_users.complete_authentication_ceremony(request, user)

        assert result.is_failure() is True
        assert result.error_type == ERROR_INACTIVE_USER
        assert result.value is None

        async with session_scope(web_app.state.database.session_factory) as session:
            result = await session.execute(select(AccessToken))
            assert result.scalars().all() == []

    try:
        asyncio.run(assert_finalisation())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_authentication_ceremony_finalisation_reloads_user_state() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    async def assert_finalisation() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(web_app.state.database.session_factory) as session:
            manager = create_user_manager(
                session, web_app.state.settings.identity_options
            )
            user = await manager.create(
                UserCreate(
                    email="stale-ceremony@example.com", password="correct horse"
                ),
                safe=True,
            )

        async with session_scope(web_app.state.database.session_factory) as session:
            current_user = await session.get(User, user.id)
            assert current_user is not None
            current_user.is_active = False
            await session.commit()

        request = Request({"type": "http", "app": web_app})
        result = await identity_users.complete_authentication_ceremony(request, user)

        assert result.is_failure() is True
        assert result.error_type == ERROR_INACTIVE_USER
        assert result.value is None

        async with session_scope(web_app.state.database.session_factory) as session:
            token_result = await session.execute(select(AccessToken))
            assert token_result.scalars().all() == []

    try:
        asyncio.run(assert_finalisation())
    finally:
        asyncio.run(close_database(web_app.state.database))


class CaptureIdentityDelivery:
    def __init__(self) -> None:
        self.reset_tokens: list[tuple[str, str]] = []
        self.verification_tokens: list[tuple[str, str]] = []

    async def send_reset_password_token(
        self,
        user: User,
        token: str,
        request: Request | None = None,
    ) -> None:
        self.reset_tokens.append((user.email, token))

    async def send_verification_token(
        self,
        user: User,
        token: str,
        request: Request | None = None,
    ) -> None:
        self.verification_tokens.append((user.email, token))


def seed_identity_user(
    web_app: FastAPI,
    *,
    email: str = "person@example.com",
    password: str = "correct horse",
    is_active: bool = True,
    is_verified: bool = False,
    expires_at: float | None = None,
) -> None:
    async def seed_user() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(web_app.state.database.session_factory) as session:
            manager = create_user_manager(
                session, web_app.state.settings.identity_options
            )
            user = await manager.create(
                UserCreate(
                    email=email,
                    password=password,
                    is_active=is_active,
                    is_verified=is_verified,
                ),
                safe=False,
            )
            if expires_at is not None:
                user.expires_at = expires_at
                await session.commit()

    asyncio.run(seed_user())


def update_identity_user(
    web_app: FastAPI,
    *,
    email: str,
    **values: object,
) -> None:
    async def update_user() -> None:
        async with session_scope(web_app.state.database.session_factory) as session:
            user = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one()
            for field_name, field_value in values.items():
                setattr(user, field_name, field_value)
            await session.commit()

    asyncio.run(update_user())


def identity_user_hashed_password(web_app: FastAPI, *, email: str) -> str:
    async def load_hashed_password() -> str:
        async with session_scope(web_app.state.database.session_factory) as session:
            user = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one()
            return user.hashed_password

    return asyncio.run(load_hashed_password())


def identity_access_token_values(web_app: FastAPI) -> list[str]:
    async def load_tokens() -> list[str]:
        async with session_scope(web_app.state.database.session_factory) as session:
            return list(await session.scalars(select(AccessToken.token)))

    return asyncio.run(load_tokens())


def csrf_token_from(response) -> str:
    match = CSRF_INPUT_PATTERN.search(response.text)
    assert match is not None
    return match.group(1)


def csrf_data(response, data: dict[str, str] | None = None) -> dict[str, str]:
    return {CSRF_FIELD_NAME: csrf_token_from(response)} | dict(data or {})


def app_request_with_session_cookie(
    web_app: FastAPI,
    *,
    session_cookie_name: str,
    session_token: str,
) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/account/logout",
            "headers": [
                (
                    b"cookie",
                    f"{session_cookie_name}={session_token}".encode("latin-1"),
                ),
            ],
            "app": web_app,
        }
    )


def test_identity_login_logout_and_current_user_routes() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)

        login_page = client.get("/account/login")
        assert login_page.status_code == 200
        assert "Sign in" in login_page.text
        assert CSRF_COOKIE_NAME in login_page.cookies
        assert f'name="{CSRF_FIELD_NAME}"' in login_page.text

        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )

        assert login_response.status_code == 303
        assert login_response.headers["location"] == "/account"
        assert login_response.cookies["uniquode_session"]
        assert "HttpOnly" in login_response.headers["set-cookie"]
        assert "Secure" not in login_response.headers["set-cookie"]

        current_user = client.get("/api/identity/current-user")
        assert current_user.status_code == 200
        assert current_user.json() == {
            "authenticated": True,
            "email": "person@example.com",
            "is_verified": False,
        }

        account_page = client.get("/account")
        assert account_page.status_code == 200
        assert "person@example.com" in account_page.text

        logout_page = client.get("/account/logout")
        assert logout_page.status_code == 200
        assert "End the current browser session." in logout_page.text

        logout_response = client.post("/account/logout", data=csrf_data(logout_page))
        assert logout_response.status_code == 303
        assert logout_response.headers["location"] == "/"
        assert "Max-Age=0" in logout_response.headers["set-cookie"]

        logged_out_user = client.get("/api/identity/current-user")
        assert logged_out_user.json() == {"authenticated": False}
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_context_provider_exposes_safe_template_user() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))

    @web_app.get("/test/template-user", include_in_schema=False)
    async def template_user_context(request: Request) -> dict[str, object]:
        context = get_request_context(request)
        user = context.get("user")
        template_user_fields = None
        if user is not None:
            template_user_fields = tuple(sorted(getattr(type(user), "__slots__", ())))
        return {
            "email": getattr(user, "email", None),
            "identity": context.get("identity"),
            "template_user_type": type(user).__name__,
            "template_user_fields": template_user_fields,
        }

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/account/login")
        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )
        assert login_response.status_code == 303

        response = client.get("/test/template-user")

        assert response.status_code == 200
        assert response.json() == {
            "email": "person@example.com",
            "identity": {
                "authenticated": True,
                "is_superuser": False,
                "is_verified": False,
            },
            "template_user_type": "TemplateUser",
            "template_user_fields": [
                "email",
                "id",
                "is_active",
                "is_superuser",
                "is_verified",
            ],
        }
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_login_uses_secure_cookie_for_https_requests() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))

    try:
        seed_identity_user(web_app)
        client = TestClient(
            web_app,
            base_url="https://testserver",
            follow_redirects=False,
        )

        login_page = client.get("/account/login")
        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )

        assert login_response.status_code == 303
        assert "Secure" in login_response.headers["set-cookie"]
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_login_can_force_secure_cookie_for_http_requests() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(session_cookie_force_secure=True),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)

        login_page = client.get("/account/login")
        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )

        assert login_response.status_code == 303
        assert "Secure" in login_response.headers["set-cookie"]
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_logout_clears_secure_cookie_for_https_requests() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))

    try:
        seed_identity_user(web_app)
        client = TestClient(
            web_app,
            base_url="https://testserver",
            follow_redirects=False,
        )

        login_page = client.get("/account/login")
        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )
        assert login_response.status_code == 303
        assert "Secure" in login_response.headers["set-cookie"]

        logout_page = client.get("/account/logout")
        logout_response = client.post("/account/logout", data=csrf_data(logout_page))

        assert logout_response.status_code == 303
        set_cookie = logout_response.headers["set-cookie"]
        assert "uniquode_session=" in set_cookie
        assert "Max-Age=0" in set_cookie
        assert "Secure" in set_cookie
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_is_not_exposed_by_default() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    try:
        client = TestClient(web_app, follow_redirects=False)

        assert client.get("/account/signup").status_code == 404
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_route_rechecks_policy_when_mounted() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
            ),
        )
    )
    web_app.state.identity_options = IdentityOptions()

    try:
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/account/login")

        assert client.get("/account/signup").status_code == 404
        submit_response = client.post(
            "/account/signup",
            data=csrf_data(
                login_page,
                {
                    "email": "signup@example.com",
                    "password": "correct horse",
                },
            ),
        )
        assert submit_response.status_code == 404
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_enabled_creates_user_without_session() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
            ),
        )
    )

    async def create_schema() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    try:
        asyncio.run(create_schema())
        client = TestClient(web_app, follow_redirects=False)
        signup_page = client.get("/account/signup")

        assert signup_page.status_code == 200
        assert "Create account" in signup_page.text

        signup_response = client.post(
            "/account/signup",
            data=csrf_data(
                signup_page,
                {
                    "email": "signup@example.com",
                    "password": "correct horse",
                },
            ),
        )

        assert signup_response.status_code == 201
        assert "Account created. You can now sign in." in signup_response.text
        assert "uniquode_session" not in signup_response.cookies

        login_page = client.get("/account/login")
        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "signup@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )

        assert login_response.status_code == 303
        assert login_response.cookies["uniquode_session"]
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_reports_existing_account_to_caller() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
            ),
        )
    )

    async def assert_duplicate_result() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        request = Request({"type": "http", "app": web_app})
        first_result = await identity_users.create_local_user_from_signup(
            request,
            email="signup@example.com",
            password="correct horse",
        )
        duplicate_result = await identity_users.create_local_user_from_signup(
            request,
            email="signup@example.com",
            password="correct horse",
        )

        assert first_result.is_ok() is True
        assert first_result.value is not None
        assert isinstance(first_result.value["id"], str)
        assert first_result.value["email"] == "signup@example.com"
        assert duplicate_result.is_failure() is True
        assert duplicate_result.error_type == ERROR_ALREADY_EXISTS
        assert duplicate_result.value is None

    try:
        asyncio.run(assert_duplicate_result())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_rejects_blank_password_before_user_creation() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
            ),
        )
    )

    async def assert_blank_password_result() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        request = Request({"type": "http", "app": web_app})
        result = await identity_users.create_local_user_from_signup(
            request,
            email="signup@example.com",
            password="",
        )

        assert result.is_failure() is True
        assert result.error_type == ERROR_INVALID_PASSWORD

        async with session_scope(web_app.state.database.session_factory) as session:
            users = (await session.execute(select(User))).scalars().all()
            assert users == []

    try:
        asyncio.run(assert_blank_password_result())
    finally:
        asyncio.run(close_database(web_app.state.database))


@pytest.mark.parametrize(
    ("password", "error_type"),
    [
        ("short 1", ERROR_PASSWORD_TOO_SHORT),
        ("abcdefghijkl", ERROR_PASSWORD_TOO_WEAK),
    ],
)
def test_public_signup_preserves_public_password_policy_error_type(
    password: str,
    error_type: str,
) -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
            ),
        )
    )

    async def assert_password_policy_result() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        request = Request({"type": "http", "app": web_app})
        result = await identity_users.create_local_user_from_signup(
            request,
            email="signup@example.com",
            password=password,
        )

        assert result.is_failure() is True
        assert result.error_type == error_type

        async with session_scope(web_app.state.database.session_factory) as session:
            users = (await session.execute(select(User))).scalars().all()
            assert users == []

    try:
        asyncio.run(assert_password_policy_result())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_maps_unknown_password_policy_error_to_invalid_password() -> None:
    class UnknownPasswordPolicy:
        def strength(
            self,
            password: str,
            user: object | None = None,
        ) -> PasswordStrength:
            del password, user
            return PasswordStrength(score=0.0, label="weak")

        def validate(
            self,
            password: str,
            user: object | None = None,
        ) -> Result[str]:
            del password, user
            return Result.failure("custom_password_denied")

    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
                password_policy=UnknownPasswordPolicy(),
            ),
        )
    )

    async def assert_password_policy_result() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        request = Request({"type": "http", "app": web_app})
        result = await identity_users.create_local_user_from_signup(
            request,
            email="signup@example.com",
            password="correct horse",
        )

        assert result.is_failure() is True
        assert result.error_type == ERROR_INVALID_PASSWORD

        async with session_scope(web_app.state.database.session_factory) as session:
            users = (await session.execute(select(User))).scalars().all()
            assert users == []

    try:
        asyncio.run(assert_password_policy_result())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_validates_password_policy_once() -> None:
    class CountingPasswordPolicy:
        calls = 0

        def strength(
            self,
            password: str,
            user: object | None = None,
        ) -> PasswordStrength:
            del password, user
            return PasswordStrength(score=1.0, label="strong")

        def validate(
            self,
            password: str,
            user: object | None = None,
        ) -> Result[str]:
            del password, user
            self.calls += 1
            return Result.ok()

    policy = CountingPasswordPolicy()
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
                password_policy=policy,
            ),
        )
    )

    async def assert_single_validation() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        request = Request({"type": "http", "app": web_app})
        result = await identity_users.create_local_user_from_signup(
            request,
            email="signup@example.com",
            password="correct horse",
        )

        assert result.is_ok() is True
        assert policy.calls == 1

    try:
        asyncio.run(assert_single_validation())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_rejects_malformed_email_before_user_creation() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
            ),
        )
    )

    async def assert_invalid_email_result() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        request = Request({"type": "http", "app": web_app})
        result = await identity_users.create_local_user_from_signup(
            request,
            email="not-an-email",
            password="correct horse",
        )

        assert result.is_failure() is True
        assert result.error_type == ERROR_INVALID_EMAIL

        async with session_scope(web_app.state.database.session_factory) as session:
            users = (await session.execute(select(User))).scalars().all()
            assert users == []

    try:
        asyncio.run(assert_invalid_email_result())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_route_returns_form_error_for_malformed_email() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
            ),
        )
    )

    async def create_schema() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    try:
        asyncio.run(create_schema())
        client = TestClient(web_app, follow_redirects=False)
        signup_page = client.get("/account/signup")

        response = client.post(
            "/account/signup",
            data=csrf_data(
                signup_page,
                {
                    "email": "not-an-email",
                    "password": "correct horse",
                },
            ),
        )

        assert response.status_code == 400
        assert "Unable to create account with those details." in response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_destroy_session_token_removes_expired_stored_token() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                session_lifetime_seconds=1,
            ),
        )
    )
    session_token = "expired-session-token"

    async def seed_expired_session_token() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(web_app.state.database.session_factory) as session:
            manager = create_user_manager(
                session, web_app.state.settings.identity_options
            )
            user = await manager.create(
                UserCreate(email="expired@example.com", password="correct horse"),
                safe=True,
            )
            session.add(
                AccessToken(
                    token=session_token,
                    user_id=user.id,
                    created_at=datetime.now(UTC) - timedelta(minutes=1),
                )
            )
            await session.commit()

    async def assert_token_removed() -> None:
        request = app_request_with_session_cookie(
            web_app,
            session_cookie_name=web_app.state.settings.identity_options.session_cookie_name,
            session_token=session_token,
        )
        await identity_users.destroy_session_token(request)

        async with session_scope(web_app.state.database.session_factory) as session:
            result = await session.execute(
                select(AccessToken).where(AccessToken.token == session_token)
            )
            assert result.scalar_one_or_none() is None

    try:
        asyncio.run(seed_expired_session_token())
        asyncio.run(assert_token_removed())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_login_requires_csrf_before_session_cookie() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)

        response = client.post(
            "/account/login",
            data={
                "email": "person@example.com",
                "password": "correct horse",
                "return_to": "/account",
            },
        )

        assert response.status_code == 403
        assert "Invalid CSRF token." in response.text
        assert "uniquode_session" not in response.cookies
    finally:
        asyncio.run(close_database(web_app.state.database))


@pytest.mark.parametrize(
    "return_to",
    [
        "https://evil.example/phish",
        "//evil.example/phish",
        "/\\evil.example/phish",
    ],
)
def test_identity_login_normalises_unsafe_return_to(return_to: str) -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)

        login_page = client.get("/account/login", params={"return_to": return_to})
        assert login_page.status_code == 200
        assert 'name="return_to" type="hidden" value="/account"' in login_page.text
        assert return_to not in login_page.text

        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": return_to,
                },
            ),
        )

        assert login_response.status_code == 303
        assert login_response.headers["location"] == "/account"
        assert login_response.cookies["uniquode_session"]
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_login_rejects_invalid_credentials() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/account/login")

        response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "incorrect",
                    "return_to": "/account",
                },
            ),
        )

        assert response.status_code == 401
        assert "Email or password is incorrect." in response.text
        assert 'id="login-form-error" role="alert"' in response.text
        assert (
            'aria-describedby="login-form-error" aria-invalid="true" autofocus'
            in response.text
        )
        assert (
            response.text.count(
                'aria-describedby="login-form-error" aria-invalid="true"'
            )
            == 2
        )
        assert "uniquode_session" not in response.cookies
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_login_failure_preserves_public_signup_link() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
            ),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/account/login")

        response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "incorrect",
                    "return_to": "/account",
                },
            ),
        )

        assert response.status_code == 401
        assert "Create account" in response.text
        assert str(web_app.url_path_for("auth:signup")) in response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_login_rejects_inactive_user() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    try:
        seed_identity_user(web_app, is_active=False)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/account/login")

        response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )

        assert response.status_code == 401
        assert "Email or password is incorrect." in response.text
        assert "uniquode_session" not in response.cookies
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_existing_session_cookie_rejects_deactivated_user() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    async def deactivate_user() -> None:
        async with session_scope(web_app.state.database.session_factory) as session:
            await session.execute(
                User.__table__.update()
                .where(User.__table__.c.email == "person@example.com")
                .values(is_active=False)
            )
            await session.commit()

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/account/login")
        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )
        assert login_response.status_code == 303
        assert login_response.cookies["uniquode_session"]

        asyncio.run(deactivate_user())

        current_user = client.get("/api/identity/current-user")

        assert current_user.status_code == 200
        assert current_user.json() == {"authenticated": False}
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_existing_session_cookie_rejects_and_revokes_expired_user() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/account/login")
        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )
        assert login_response.status_code == 303
        session_token = login_response.cookies["uniquode_session"]
        assert identity_access_token_values(web_app) == [session_token]

        update_identity_user(web_app, email="person@example.com", expires_at=1.0)

        current_user = client.get("/api/identity/current-user")

        assert current_user.status_code == 200
        assert current_user.json() == {"authenticated": False}
        assert identity_access_token_values(web_app) == []
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_dependency_helpers_handle_required_and_anonymous_users() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )

    @web_app.get("/test/required-user")
    async def required_user(request: Request) -> dict[str, str]:
        user = await require_current_user(request)
        return {"email": user.email}

    @web_app.get("/test/anonymous-user")
    async def anonymous_user(request: Request) -> dict[str, bool]:
        await require_anonymous_user(request)
        return {"anonymous": True}

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)

        unauthenticated_required = client.get("/test/required-user")
        assert unauthenticated_required.status_code == 401
        assert unauthenticated_required.headers["content-type"].startswith("text/html")
        assert "Authentication required." in unauthenticated_required.text

        anonymous_response = client.get("/test/anonymous-user")
        assert anonymous_response.status_code == 200
        assert anonymous_response.json() == {"anonymous": True}

        login_page = client.get("/account/login")
        client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )

        authenticated_required = client.get("/test/required-user")
        assert authenticated_required.status_code == 200
        assert authenticated_required.json() == {"email": "person@example.com"}

        authenticated_anonymous = client.get("/test/anonymous-user")
        assert authenticated_anonymous.status_code == 403
        assert "Already authenticated." in authenticated_anonymous.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_resolve_current_user_caches_result_per_request(monkeypatch) -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(),
        )
    )
    read_count = 0

    @web_app.get("/test/current-user-cache")
    async def current_user_cache(request: Request) -> dict[str, object]:
        first = await identity_users.resolve_current_user(request)
        second = await identity_users.resolve_current_user(request)
        return {
            "first": first.email if first is not None else None,
            "second": second.email if second is not None else None,
            "same_object": first is second,
        }

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/account/login")
        login_response = client.post(
            "/account/login",
            data=csrf_data(
                login_page,
                {
                    "email": "person@example.com",
                    "password": "correct horse",
                    "return_to": "/account",
                },
            ),
        )
        assert login_response.status_code == 303

        original_create_database_strategy = identity_users.create_database_strategy

        def counting_create_database_strategy(session, options):
            strategy = original_create_database_strategy(session, options)

            class CountingStrategy:
                async def read_token(self, token, user_manager):
                    nonlocal read_count
                    read_count += 1
                    return await strategy.read_token(token, user_manager)

                async def destroy_token(self, token, user):
                    return await strategy.destroy_token(token, user)

            return CountingStrategy()

        monkeypatch.setattr(
            identity_users,
            "create_database_strategy",
            counting_create_database_strategy,
        )

        response = client.get("/test/current-user-cache")

        assert response.status_code == 200
        assert response.json() == {
            "first": "person@example.com",
            "second": "person@example.com",
            "same_object": True,
        }
        assert read_count == 1
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_password_reset_route_uses_delivery_hook() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        reset_page = client.get("/account/password/reset")

        response = client.post(
            "/account/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )

        assert response.status_code == 200
        assert delivery.reset_tokens
        assert delivery.reset_tokens[0][0] == "person@example.com"

        confirm_response = client.post(
            "/account/password/reset/confirm",
            data=csrf_data(
                response,
                {
                    "token": delivery.reset_tokens[0][1],
                    "password": "new correct horse",
                },
            ),
        )

        assert confirm_response.status_code == 200
        assert "Password reset complete." in confirm_response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_password_reset_confirm_returns_html_error_for_invalid_token() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        reset_page = client.get("/account/password/reset")

        response = client.post(
            "/account/password/reset/confirm",
            data=csrf_data(
                reset_page,
                {"token": "invalid", "password": "new correct horse"},
            ),
        )

        assert response.status_code == 400
        assert response.headers["content-type"].startswith("text/html")
        assert "The reset token is invalid or expired." in response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_password_reset_confirm_rejects_blank_password() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        reset_page = client.get("/account/password/reset")

        response = client.post(
            "/account/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )
        assert response.status_code == 200
        assert delivery.reset_tokens

        confirm_response = client.post(
            "/account/password/reset/confirm",
            data=csrf_data(
                response,
                {
                    "token": delivery.reset_tokens[0][1],
                    "password": " ",
                },
            ),
        )

        assert confirm_response.status_code == 400
        assert "The reset token is invalid or expired." in confirm_response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_password_reset_request_ignores_inactive_user() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(web_app, is_active=False)
        client = TestClient(web_app, follow_redirects=False)
        reset_page = client.get("/account/password/reset")

        response = client.post(
            "/account/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )

        assert response.status_code == 200
        assert "If the account exists, a reset link has been queued." in response.text
        assert delivery.reset_tokens == []
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_password_reset_request_ignores_expired_user() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(web_app, expires_at=1.0)
        client = TestClient(web_app, follow_redirects=False)
        reset_page = client.get("/account/password/reset")

        response = client.post(
            "/account/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )

        assert response.status_code == 200
        assert "If the account exists, a reset link has been queued." in response.text
        assert delivery.reset_tokens == []
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_password_reset_confirm_rejects_user_expired_after_token_issue() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        reset_page = client.get("/account/password/reset")

        response = client.post(
            "/account/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )
        assert response.status_code == 200
        assert delivery.reset_tokens

        original_hashed_password = identity_user_hashed_password(
            web_app,
            email="person@example.com",
        )
        update_identity_user(web_app, email="person@example.com", expires_at=1.0)

        confirm_response = client.post(
            "/account/password/reset/confirm",
            data=csrf_data(
                response,
                {
                    "token": delivery.reset_tokens[0][1],
                    "password": "new correct horse",
                },
            ),
        )

        assert confirm_response.status_code == 400
        assert "The reset token is invalid or expired." in confirm_response.text
        assert (
            identity_user_hashed_password(web_app, email="person@example.com")
            == original_hashed_password
        )
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_password_reset_confirm_rejects_user_inactive_after_token_issue() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        reset_page = client.get("/account/password/reset")

        response = client.post(
            "/account/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )
        assert response.status_code == 200
        assert delivery.reset_tokens

        original_hashed_password = identity_user_hashed_password(
            web_app,
            email="person@example.com",
        )
        update_identity_user(web_app, email="person@example.com", is_active=False)

        confirm_response = client.post(
            "/account/password/reset/confirm",
            data=csrf_data(
                response,
                {
                    "token": delivery.reset_tokens[0][1],
                    "password": "new correct horse",
                },
            ),
        )

        assert confirm_response.status_code == 400
        assert "The reset token is invalid or expired." in confirm_response.text
        assert (
            identity_user_hashed_password(web_app, email="person@example.com")
            == original_hashed_password
        )
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_verification_route_uses_delivery_hook() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        verify_page = client.get("/account/verify")

        response = client.post(
            "/account/verify",
            data=csrf_data(verify_page, {"email": "person@example.com"}),
        )

        assert response.status_code == 200
        assert delivery.verification_tokens
        assert delivery.verification_tokens[0][0] == "person@example.com"

        confirm_response = client.post(
            "/account/verify/confirm",
            data=csrf_data(response, {"token": delivery.verification_tokens[0][1]}),
        )

        assert confirm_response.status_code == 200
        assert "Email verification complete." in confirm_response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_verification_confirm_rejects_user_deactivated_after_token_request() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    async def deactivate_user() -> None:
        async with session_scope(web_app.state.database.session_factory) as session:
            await session.execute(
                User.__table__.update()
                .where(User.__table__.c.email == "person@example.com")
                .values(is_active=False)
            )
            await session.commit()

    async def assert_unverified() -> None:
        async with session_scope(web_app.state.database.session_factory) as session:
            result = await session.execute(
                select(User).where(User.email == "person@example.com")
            )
            user = result.scalar_one()
            assert user.is_verified is False

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        verify_page = client.get("/account/verify")

        response = client.post(
            "/account/verify",
            data=csrf_data(verify_page, {"email": "person@example.com"}),
        )
        assert response.status_code == 200
        assert delivery.verification_tokens

        asyncio.run(deactivate_user())
        token = delivery.verification_tokens[0][1]
        verification_result = asyncio.run(
            identity_users.verify_user(Request({"type": "http", "app": web_app}), token)
        )
        assert verification_result.is_failure() is True
        assert verification_result.error_type == ERROR_INACTIVE_USER

        confirm_response = client.post(
            "/account/verify/confirm",
            data=csrf_data(response, {"token": token}),
        )

        assert confirm_response.status_code == 400
        assert "The verification token is invalid or expired." in confirm_response.text
        asyncio.run(assert_unverified())
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_verification_confirm_rejects_email_changed_after_token_request() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    async def change_email() -> None:
        async with session_scope(web_app.state.database.session_factory) as session:
            await session.execute(
                User.__table__.update()
                .where(User.__table__.c.email == "person@example.com")
                .values(email="renamed@example.com")
            )
            await session.commit()

    async def assert_unverified() -> None:
        async with session_scope(web_app.state.database.session_factory) as session:
            result = await session.execute(
                select(User).where(User.email == "renamed@example.com")
            )
            user = result.scalar_one()
            assert user.is_verified is False

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        verify_page = client.get("/account/verify")

        response = client.post(
            "/account/verify",
            data=csrf_data(verify_page, {"email": "person@example.com"}),
        )
        assert response.status_code == 200
        assert delivery.verification_tokens

        asyncio.run(change_email())
        token = delivery.verification_tokens[0][1]
        verification_result = asyncio.run(
            identity_users.verify_user(Request({"type": "http", "app": web_app}), token)
        )
        assert verification_result.is_failure() is True
        assert verification_result.error_type == ERROR_IDENTITY_CHANGED

        confirm_response = client.post(
            "/account/verify/confirm",
            data=csrf_data(response, {"token": token}),
        )

        assert confirm_response.status_code == 400
        assert "The verification token is invalid or expired." in confirm_response.text
        asyncio.run(assert_unverified())
    finally:
        asyncio.run(close_database(web_app.state.database))


@pytest.mark.parametrize(
    ("is_active", "is_verified"),
    [
        (False, False),
        (True, True),
    ],
)
def test_verification_request_ignores_ineligible_user(
    is_active: bool,
    is_verified: bool,
) -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(
            web_app,
            is_active=is_active,
            is_verified=is_verified,
        )
        client = TestClient(web_app, follow_redirects=False)
        verify_page = client.get("/account/verify")

        response = client.post(
            "/account/verify",
            data=csrf_data(verify_page, {"email": "person@example.com"}),
        )

        assert response.status_code == 200
        assert (
            "If the account can be verified, a verification link has been queued."
            in response.text
        )
        assert delivery.verification_tokens == []
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_verification_confirm_returns_html_error_for_invalid_token() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        verify_page = client.get("/account/verify")
        verification_result = asyncio.run(
            identity_users.verify_user(
                Request({"type": "http", "app": web_app}),
                "invalid",
            )
        )

        assert verification_result.is_failure() is True
        assert verification_result.error_type == ERROR_INVALID_TOKEN

        response = client.post(
            "/account/verify/confirm",
            data=csrf_data(verify_page, {"token": "invalid"}),
        )

        assert response.status_code == 400
        assert response.headers["content-type"].startswith("text/html")
        assert "The verification token is invalid or expired." in response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_initial_admin_bootstrap_creates_first_admin() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    async def assert_bootstrap() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(session_factory) as session:
            result = await bootstrap_initial_admin(
                session,
                settings.identity_options,
                InitialAdminCredentials(
                    email="admin@example.com",
                    password="correct horse",
                ),
            )

            assert result.created is True
            assert result.user.email == "admin@example.com"
            assert result.user.is_superuser is True
            assert result.user.is_verified is True

    try:
        asyncio.run(assert_bootstrap())
    finally:
        asyncio.run(close_database(engine))


def test_initial_admin_bootstrap_does_not_create_second_admin() -> None:
    settings = Settings(database_url=SQLITE_MEMORY_DATABASE_URL)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    async def assert_bootstrap() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(session_factory) as session:
            first = await bootstrap_initial_admin(
                session,
                settings.identity_options,
                InitialAdminCredentials(
                    email="admin@example.com",
                    password="correct horse",
                ),
            )
            second = await bootstrap_initial_admin(
                session,
                settings.identity_options,
                InitialAdminCredentials(
                    email="other-admin@example.com",
                    password="correct horse",
                ),
            )

            assert first.created is True
            assert second.created is False
            assert second.user.id == first.user.id
            assert second.user.email == "admin@example.com"

    try:
        asyncio.run(assert_bootstrap())
    finally:
        asyncio.run(close_database(engine))


def test_initial_admin_bootstrap_is_single_writer_under_concurrency(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "identity.sqlite3"
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{database_path.as_posix()}",
    )
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    async def assert_bootstrap() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async def run_bootstrap(email: str):
            async with session_scope(session_factory) as session:
                return await bootstrap_initial_admin(
                    session,
                    settings.identity_options,
                    InitialAdminCredentials(
                        email=email,
                        password="correct horse",
                    ),
                )

        first, second = await asyncio.gather(
            run_bootstrap("first-admin@example.com"),
            run_bootstrap("second-admin@example.com"),
        )

        async with session_scope(session_factory) as session:
            admins = (
                (await session.execute(select(User).where(User.is_superuser.is_(True))))
                .scalars()
                .all()
            )
            bootstrap_claim_count = await session.scalar(
                select(func.count()).select_from(InitialAdminBootstrap)
            )

        assert len([result for result in (first, second) if result.created]) == 1
        assert len(admins) == 1
        assert bootstrap_claim_count == 1
        assert {first.user.id, second.user.id} == {admins[0].id}

    try:
        asyncio.run(assert_bootstrap())
    finally:
        asyncio.run(close_database(engine))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, DEFAULT_RELOAD),
        ("1", True),
        ("true", True),
        ("on", True),
        ("false", False),
        ("off", False),
    ],
)
def test_env_requests_reload_normalises_values(
    value: str | None, expected: bool
) -> None:
    assert env_requests_reload(value) is expected


@pytest.mark.parametrize("prefix", ["", "/", "   "])
def test_route_contract_rejects_empty_or_root_prefixes(prefix: str) -> None:
    with pytest.raises(ValueError, match="must not be empty or root-mounted"):
        _normalise_path_prefix(prefix)


def test_home_page_renders_full_html_document() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "<!doctype html>" in response.text.lower()
    assert 'data-route-name="public:home"' in response.text
    assert 'href="/static/styles/app.css"' in response.text
    assert 'src="https://unpkg.com/htmx.org@' in response.text
    assert 'class="page-tools"' in response.text
    assert 'id="theme-selector"' in response.text


def test_partial_route_renders_fragment_only() -> None:
    client = TestClient(create_app())

    response = client.get("/partials/theme-selector")

    assert response.status_code == 200
    assert "<!doctype html>" not in response.text.lower()
    assert 'id="theme-selector"' in response.text
    assert 'action="http://testserver/partials/theme-mode"' in response.text


def test_api_route_stays_machine_oriented() -> None:
    client = TestClient(create_app())

    response = client.get("/api/web/theme")

    assert response.status_code == 200
    assert response.json() == {"theme_mode": "auto"}


def test_missing_page_route_renders_html_404() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/missing")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert "<!doctype html>" in response.text.lower()
    assert "Not Found" in response.text


def test_missing_api_route_stays_json_even_with_browser_accept_header() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/api/missing", headers={"accept": "text/html"})

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": "Not Found",
        "detail": "The requested resource could not be found.",
        "status_code": 404,
    }


def test_page_route_unhandled_error_renders_html_500() -> None:
    web_app = create_app()

    @web_app.get("/boom-page")
    async def boom_page() -> None:
        raise RuntimeError("boom")

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get("/boom-page")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("text/html")
    assert "<!doctype html>" in response.text.lower()
    assert "Internal Server Error" in response.text


def test_api_route_unhandled_error_stays_json() -> None:
    web_app = create_app()

    @web_app.get("/api/test/boom")
    async def boom_api() -> None:
        raise RuntimeError("boom")

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get("/api/test/boom", headers={"accept": "text/html"})

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": "Internal Server Error",
        "detail": "An internal server error prevented the request from completing.",
        "status_code": 500,
    }


def test_partial_route_unhandled_error_returns_fragment() -> None:
    web_app = create_app()

    @web_app.get("/partials/boom")
    async def boom_partial() -> None:
        raise RuntimeError("boom")

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get("/partials/boom", headers={"HX-Request": "true"})

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("text/html")
    assert "<!doctype html>" not in response.text.lower()
    assert "<section" in response.text
    assert "Internal Server Error" in response.text


def test_missing_partial_route_returns_fragment_404() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/partials/missing", headers={"HX-Request": "true"})

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert "<!doctype html>" not in response.text.lower()
    assert "<section" in response.text
    assert "Not Found" in response.text


def test_http_exception_preserves_headers() -> None:
    web_app = create_app()

    @web_app.get("/api/test/auth")
    async def auth_api() -> None:
        raise HTTPException(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get("/api/test/auth")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_method_not_allowed_preserves_allow_header() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.post("/health")

    assert response.status_code == 405
    assert response.headers["allow"] == "GET"


def test_error_handler_falls_back_when_renderer_is_missing() -> None:
    web_app = create_app()
    del web_app.state.renderer

    @web_app.get("/boom-fallback")
    async def boom_fallback() -> None:
        raise RuntimeError("boom")

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get("/boom-fallback")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("text/plain")
    assert "500 Internal Server Error" in response.text


def test_page_validation_error_renders_field_summary() -> None:
    web_app = create_app()

    @web_app.get("/validate-page")
    async def validate_page(required_count: int) -> dict[str, int]:
        return {"required_count": required_count}

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get("/validate-page", params={"required_count": "nope"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("text/html")
    assert "The request was invalid." in response.text
    assert "<strong>required_count</strong>" in response.text


def test_partial_validation_error_renders_fragment_field_summary() -> None:
    web_app = create_app()

    @web_app.get("/partials/validate")
    async def validate_partial(required_count: int) -> dict[str, int]:
        return {"required_count": required_count}

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get(
        "/partials/validate",
        params={"required_count": "nope"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("text/html")
    assert "<!doctype html>" not in response.text.lower()
    assert "<strong>required_count</strong>" in response.text


def test_known_http_status_uses_generic_api_fallback() -> None:
    web_app = create_app()

    @web_app.get("/api/test/limited")
    async def limited_api() -> None:
        raise HTTPException(status_code=429)

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get("/api/test/limited")

    assert response.status_code == 429
    assert response.json() == {
        "error": "Too Many Requests",
        "detail": "Too many requests were made in a short period.",
        "status_code": 429,
    }


def test_non_standard_empty_body_error_bypasses_generic_rendering() -> None:
    web_app = create_app()

    @web_app.get("/api/test/terminate")
    async def terminate_api() -> None:
        raise EmptyBodyResponseException(status_code=444)

    client = TestClient(web_app, raise_server_exceptions=False)
    response = client.get("/api/test/terminate")

    assert response.status_code == 444
    assert response.text == ""
    assert "content-type" not in response.headers


def test_theme_preference_cookie_drives_page_rendering() -> None:
    client = TestClient(create_app())
    client.cookies.set("theme_mode", "dark")

    response = client.get("/")

    assert response.status_code == 200
    assert 'data-theme="dark"' in response.text
    assert "Theme mode: Dark" in response.text


def test_theme_mode_route_sets_cookie_and_returns_fragment() -> None:
    client = TestClient(create_app())
    home_page = client.get("/")

    response = client.post(
        "/partials/theme-mode",
        data=csrf_data(home_page, {"theme_mode": "light", "return_to": "/"}),
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert response.cookies["theme_mode"] == "light"
    assert "HttpOnly" in response.headers["set-cookie"]
    assert json.loads(response.headers["HX-Trigger"]) == {
        "theme-mode-changed": {"theme_mode": "light"}
    }
    assert 'id="theme-selector"' in response.text
    assert '/partials/theme-mode"' in response.text
    assert 'name="theme_mode" value="dark"' in response.text
    assert "Theme mode: Light." in response.text


def test_theme_mode_route_normalises_invalid_value_to_auto() -> None:
    client = TestClient(create_app())
    home_page = client.get("/")

    response = client.post(
        "/partials/theme-mode",
        data=csrf_data(home_page, {"theme_mode": "neon", "return_to": "/"}),
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert response.cookies["theme_mode"] == "auto"
    assert "HttpOnly" in response.headers["set-cookie"]
    assert json.loads(response.headers["HX-Trigger"]) == {
        "theme-mode-changed": {"theme_mode": "auto"}
    }
    assert 'id="theme-selector"' in response.text
    assert '/partials/theme-mode"' in response.text
    assert "Theme mode: Auto." in response.text
    assert 'name="theme_mode" value="light"' in response.text


def test_theme_mode_route_redirects_without_htmx() -> None:
    client = TestClient(create_app(), follow_redirects=False)
    home_page = client.get("/")

    response = client.post(
        "/partials/theme-mode",
        data=csrf_data(home_page, {"theme_mode": "dark", "return_to": "/"}),
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert response.cookies["theme_mode"] == "dark"
    assert "HttpOnly" in response.headers["set-cookie"]


@pytest.mark.parametrize(
    "return_to",
    [
        "https://evil.example/theme",
        "//evil.example/theme",
        "/\\evil.example/theme",
    ],
)
def test_theme_mode_route_normalises_unsafe_redirect_return_to(
    return_to: str,
) -> None:
    client = TestClient(create_app(), follow_redirects=False)
    home_page = client.get("/")

    response = client.post(
        "/partials/theme-mode",
        data=csrf_data(home_page, {"theme_mode": "dark", "return_to": return_to}),
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert response.cookies["theme_mode"] == "dark"


def test_theme_mode_route_normalises_unsafe_htmx_return_to() -> None:
    client = TestClient(create_app())
    home_page = client.get("/")
    return_to = "https://evil.example/theme"

    response = client.post(
        "/partials/theme-mode",
        data=csrf_data(home_page, {"theme_mode": "dark", "return_to": return_to}),
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert return_to not in response.text
    assert 'name="return_to" value="/"' in response.text
    assert response.cookies["theme_mode"] == "dark"


def test_theme_mode_route_handles_malformed_form_body_with_csrf_header() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    home_page = client.get("/")

    response = client.post(
        "/partials/theme-mode",
        content=b"--broken\r\nnot-form-data",
        headers={
            "HX-Request": "true",
            CSRF_HEADER_NAME: csrf_token_from(home_page),
            "content-type": "multipart/form-data; boundary=broken",
        },
    )

    assert response.status_code == 200
    assert response.cookies["theme_mode"] == "auto"


def test_theme_mode_route_requires_csrf() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/partials/theme-mode",
        data={"theme_mode": "dark", "return_to": "/"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 403
    assert "Invalid CSRF token." in response.text
    assert "theme_mode" not in response.cookies


def test_theme_mode_route_accepts_csrf_header() -> None:
    client = TestClient(create_app())
    home_page = client.get("/")

    response = client.post(
        "/partials/theme-mode",
        data={"theme_mode": "dark", "return_to": "/"},
        headers={
            "HX-Request": "true",
            CSRF_HEADER_NAME: csrf_token_from(home_page),
        },
    )

    assert response.status_code == 200
    assert response.cookies["theme_mode"] == "dark"


def test_theme_mode_route_rejects_csrf_header_without_cookie() -> None:
    token_client = TestClient(create_app())
    home_page = token_client.get("/")

    client = TestClient(create_app())
    response = client.post(
        "/partials/theme-mode",
        data={"theme_mode": "dark", "return_to": "/"},
        headers={
            "HX-Request": "true",
            CSRF_HEADER_NAME: csrf_token_from(home_page),
        },
    )

    assert response.status_code == 403
    assert "theme_mode" not in response.cookies


def test_home_page_renders_reusable_theme_selector_component() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.text.count('id="theme-selector"') == 1
    assert response.text.index('class="page-tools"') < response.text.index("<main")
    assert 'method="post"' in response.text
    assert 'name="theme_mode" value="light"' in response.text
    assert (
        'aria-label="Theme mode: Auto. Activate to switch to Light."' in response.text
    )


def test_earlier_application_module_can_override_wevra_auth_identity_template(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_root = tmp_path / "identity_override_app"
    template_root = package_root / "templates/identity/pages"
    template_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (template_root / "login.html").write_text(
        """
        {% extends "layouts/page.html" %}
        {% block content %}
        <h1>Overridden login</h1>
        {% endblock %}
        """,
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            project_root=tmp_path,
            app_config=build_test_app_config(
                tmp_path,
                modules=(
                    "identity_override_app",
                    "wevra.web",
                    "wevra.auth",
                ),
            ),
        )
    )

    try:
        response = TestClient(web_app).get("/account/login")

        assert response.status_code == 200
        assert "Overridden login" in response.text
        assert 'autocomplete="email"' not in response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_create_app_applies_configured_template_cache_options() -> None:
    renderer = create_app().state.renderer

    assert renderer.auto_reload is True
    assert renderer.cache_size == 0
    assert renderer.environment.auto_reload is True
