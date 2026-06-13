import ast
import asyncio
import importlib
import inspect
import json
import logging
import os
import re
import sqlite3
import tomllib
from dataclasses import replace
from pathlib import Path
from textwrap import dedent

import click
import pytest
import wevra.db.migrate as data_migrate_module
import wevra.tools.migrate as migrate_module
import wevra.tools.runserver as runserver_module
from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import select
from starlette.staticfiles import StaticFiles
from wevra import get_site
from wevra.auth import AuthCapability
from wevra.auth.accounts.schemas import UserCreate
from wevra.auth.models import (
    AccessToken,
    Base,
    User,
)
from wevra.auth.sessions import (
    create_user_manager,
)
from wevra.core.composition import (
    AppConfig,
    RouteOptions,
    StaticOptions,
    TemplateOptions,
)
from wevra.db import DatabaseCapability
from wevra.db.migration_metadata import (
    MigrationConfigError,
)
from wevra.db.persistence import (
    close_database,
    create_database_engine,
    is_supported_database_url,
    sqlite_database_path,
)
from wevra.tools.project import (
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
from wevra.web.forms.csrf import (
    CSRF_FIELD_NAME,
    CSRF_HEADER_NAME,
)
from wevra.web.routes.contracts import _normalise_path_prefix
from wevra.web.security import COOP_HEADER_NAME

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
    load_environment,
)
from app.routes.health import health
from app.settings import (
    SQLITE_MEMORY_DATABASE_URL,
    Settings,
    load_settings,
)

CSRF_INPUT_PATTERN = re.compile(
    rf'<input[^>]+name="{CSRF_FIELD_NAME}"[^>]+value="([^"]+)"'
)


IDENTITY_TABLE_NAMES = frozenset(
    {
        "identity_user",
        "identity_access_token",
        "identity_provider",
        "identity_external_identity_link",
    },
)
TEST_ROUTE_PREFIXES = {
    "app": {"default": ""},
    "wevra.web": {"partials": "", "api": ""},
    "wevra.db": {},
    "wevra.auth": {"account": "/account", "api": ""},
}


def assert_identity_tables_present(table_names: set[str]) -> None:
    assert IDENTITY_TABLE_NAMES.issubset(table_names)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        f"{node.module}.{alias.name}"
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
        for alias in node.names
    )
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    return imported_modules


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
    modules: tuple[str, ...] = ("app", "wevra.web", "wevra.db", "wevra.auth"),
    route_prefixes: dict[str, dict[str, str]] | None = None,
    static_url_path: str = "/static/",
    static_export_root: str = "static",
    database_url: str = "sqlite+aiosqlite:///app.sqlite3",
    auth_options: dict[str, object] | None = None,
) -> Path:
    prefixes = {
        module_name: dict(TEST_ROUTE_PREFIXES[module_name])
        for module_name in modules
        if module_name in TEST_ROUTE_PREFIXES
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
        session_cookie_name = "test_session"
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
        module_name: dict(TEST_ROUTE_PREFIXES[module_name])
        for module_name in modules
        if module_name in TEST_ROUTE_PREFIXES
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
        auth=(
            {
                "session_cookie_name": "test_session",
                "session_cookie_force_secure": False,
            }
            if "wevra.auth" in modules
            else None
        ),
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


def test_create_app_uses_wevra_lifespan_startup_for_configured_routes() -> None:
    with TestClient(create_app()) as client:
        login_response = client.get("/account/login")
        static_response = client.get("/static/styles/app.css")

    assert login_response.status_code == 200
    assert static_response.status_code == 200
    assert any(
        isinstance(route, APIRoute) and route.path == "/health"
        for route in client.app.routes
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


def test_app_runtime_does_not_import_wevra_owned_configuration_details() -> None:
    app_root = Path(__file__).resolve().parents[1] / "src/app"
    forbidden_imports = {
        "wevra.auth.configuration",
        "wevra.auth.settings",
        "wevra.db.migrate",
        "wevra.db.surfaces",
    }
    imported_modules = {
        module for path in app_root.rglob("*.py") for module in _imported_modules(path)
    }

    assert imported_modules.isdisjoint(forbidden_imports)


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
            "heads",
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
            "heads",
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


def test_create_app_mounts_configurable_static_files() -> None:
    settings = Settings(
        static_root=Path("src/test-static"),
        static_url_path="/assets/",
    )

    web_app = create_app(settings)

    with TestClient(web_app):
        static_routes = [
            route
            for route in web_app.routes
            if getattr(route, "name", None) == "static"
        ]
    assert len(static_routes) == 1

    static_route = static_routes[0]
    assert static_route.path == "/assets"

    static_app = static_route.app
    assert isinstance(static_app, StaticFiles)
    assert Path(static_app.directory) == settings.static_root


def test_create_app_serves_static_files_from_configured_modules() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/static/styles/app.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert "--web-core-colour-page-bg" in response.text


def test_create_app_omitting_wevra_web_mounts_empty_static_route(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            project_root=tmp_path,
            app_config=build_test_app_config(tmp_path, modules=("app",)),
        )
    )

    with TestClient(app) as client:
        response = client.get("/static/styles/app.css")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert "--web-core-colour-page-bg" not in response.text


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
    app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            project_root=tmp_path,
            app_config=build_test_app_config(
                tmp_path,
                modules=("prefixed_route_app", "wevra.web"),
                route_prefixes={"prefixed_route_app": {"default": "/tools"}},
            ),
        )
    )

    with TestClient(app) as client:
        assert client.get("/tools/ping").text == "prefixed"
        assert client.get("/ping").status_code == 404


def test_create_app_registers_routes_only_from_configured_modules(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            project_root=tmp_path,
            app_config=build_test_app_config(tmp_path, modules=("app", "wevra.web")),
        )
    )

    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/account/login").status_code == 404
        assert client.get("/health").status_code == 200


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

    with TestClient(web_app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.text == "filesystem template override"


def test_missing_static_asset_does_not_render_html_error_page() -> None:
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.get("/static/missing.css")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/plain")
    assert "<!doctype html>" not in response.text.lower()
    assert response.text == "Not Found"


def test_create_app_applies_default_cross_origin_opener_policy() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))

    with TestClient(web_app) as client:
        response = client.get("/")

    assert response.headers[COOP_HEADER_NAME] == "same-origin"


def test_create_app_can_disable_cross_origin_opener_policy() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            cross_origin_opener_policy=None,
        )
    )

    with TestClient(web_app) as client:
        response = client.get("/")

    assert COOP_HEADER_NAME not in response.headers


def test_settings_default_resource_roots_are_not_filesystem_overrides(
    tmp_path: Path,
) -> None:
    settings = Settings(project_root=tmp_path)

    assert settings.app_config is None
    assert settings.modules == ()
    assert settings.route_prefixes == {}
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
        modules=("app", "wevra.db", "wevra.auth"),
        static_url_path="/assets/",
        database_url="sqlite+aiosqlite:///identity.sqlite3",
    )

    settings = load_settings(environ={}, project_root=tmp_path, read_dotenv=False)

    assert settings.app_config is not None
    assert settings.app_config.config_path == config_path.resolve()
    assert settings.app_config.database_url == "sqlite+aiosqlite:///identity.sqlite3"
    assert settings.modules == ("app", "wevra.db", "wevra.auth")
    assert settings.template_auto_reload is True
    assert settings.template_cache_size == 0
    assert settings.template_root is None
    assert settings.static_root is None
    assert settings.static_mount_path == "/assets"
    assert settings.database_url == sqlite_file_url(tmp_path / "identity.sqlite3")


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
    settings = load_settings(
        environ={
            ENV_APP_NAME: "env-app",
            ENV_APP_ENV: "production",
            ENV_DATABASE_URL: database_url,
            ENV_CSRF_SECRET: "csrf-secret",
            ENV_CSRF_SECURE: "true",
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
    assert settings.static_mount_path == "/assets"


def test_load_settings_reads_local_dotenv(tmp_path) -> None:
    write_app_config(tmp_path / "app.toml")
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "APP_NAME=dotenv-app",
                "DATABASE_URL=sqlite+aiosqlite:///dotenv.sqlite3",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_settings(environ={}, project_root=tmp_path)

    assert settings.app_name == "dotenv-app"
    assert settings.database_url == (
        f"sqlite+aiosqlite:///{(tmp_path / 'dotenv.sqlite3').resolve().as_posix()}"
    )


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


def test_settings_logs_generated_local_csrf_token_secret(caplog) -> None:
    caplog.set_level(logging.INFO, logger="app.settings")

    settings = Settings()

    assert settings.csrf_token_secret_configured is False
    assert "Generated startup-local CSRF token secret." in caplog.text


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

    assert settings.modules == ("app", "wevra.web")
    assert settings.csrf_cookie_secure is True


def test_settings_preserves_configured_auth_module(tmp_path: Path) -> None:
    settings = Settings(
        app_config=AppConfig(
            config_path=(tmp_path / "app.toml").resolve(),
            project_root=tmp_path.resolve(),
            modules=("app", "wevra.web", "wevra.db", "wevra.auth"),
            routes=RouteOptions(prefixes={}),
            templates=TemplateOptions(auto_reload=True, cache_size=0),
            static=StaticOptions(url_path="/static/", export_root=Path("static")),
            auth={},
        )
    )

    assert settings.modules == ("app", "wevra.web", "wevra.db", "wevra.auth")


def test_non_local_settings_require_configured_csrf_token_secret() -> None:
    with pytest.raises(
        ConfigurationError,
        match="Non-local deployments must configure a stable CSRF token secret",
    ):
        Settings(
            deployment_environment="production",
        )

    with pytest.raises(ConfigurationError, match="CSRF token secret must not be blank"):
        Settings(
            deployment_environment="production",
            csrf_token_secret="   ",
        )

    with pytest.raises(
        ConfigurationError,
        match="Non-local deployments must use secure CSRF cookies",
    ):
        Settings(
            deployment_environment="production",
            csrf_token_secret="production-csrf-secret",
            csrf_cookie_secure=False,
        )


def test_create_app_configures_database_and_identity_boundaries() -> None:
    with TestClient(create_app()) as client:
        site = get_site(client.app)
        database = site.require_capability(DatabaseCapability)
        auth = site.require_capability(AuthCapability)

    assert isinstance(database, DatabaseCapability)
    assert isinstance(auth, AuthCapability)
    assert not hasattr(client.app.state, "identity_options")


def test_create_app_without_explicit_settings_uses_environment(
    tmp_path,
    monkeypatch,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'app.sqlite3').as_posix()}"
    monkeypatch.setenv(ENV_APP_NAME, "environment-app")
    monkeypatch.setenv(ENV_DATABASE_URL, database_url)

    web_app = create_app()

    with TestClient(web_app):
        assert web_app.title == "environment-app"
        assert web_app.state.settings.database_url == database_url


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
        database = get_site(web_app).require_capability(DatabaseCapability)
        auth = get_site(web_app).require_capability(AuthCapability)
        async with database.transaction() as session:
            await session.run_sync(
                lambda sync_session: Base.metadata.create_all(
                    bind=sync_session.get_bind()
                )
            )
            manager = create_user_manager(session, auth.settings.identity_options)
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
        database = get_site(web_app).require_capability(DatabaseCapability)
        async with database.transaction() as session:
            user = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one()
            for field_name, field_value in values.items():
                setattr(user, field_name, field_value)
            await session.commit()

    asyncio.run(update_user())


def identity_user_hashed_password(web_app: FastAPI, *, email: str) -> str:
    async def load_hashed_password() -> str:
        database = get_site(web_app).require_capability(DatabaseCapability)
        async with database.session() as session:
            user = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one()
            return user.hashed_password

    return asyncio.run(load_hashed_password())


def identity_access_token_values(web_app: FastAPI) -> list[str]:
    async def load_tokens() -> list[str]:
        database = get_site(web_app).require_capability(DatabaseCapability)
        async with database.session() as session:
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
    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "<!doctype html>" in response.text.lower()
    assert 'data-route-name="public:home"' in response.text
    assert 'href="/static/styles/app.css"' in response.text
    assert 'src="https://unpkg.com/htmx.org@' in response.text
    assert 'class="page-tools"' in response.text
    assert 'id="theme-selector"' in response.text


def test_api_route_stays_machine_oriented() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/web/theme")

    assert response.status_code == 200
    assert response.json() == {"theme_mode": "auto"}


def test_theme_preference_cookie_drives_page_rendering() -> None:
    with TestClient(create_app()) as client:
        client.cookies.set("theme_mode", "dark")

        response = client.get("/")

    assert response.status_code == 200
    assert 'data-theme="dark"' in response.text
    assert "Theme mode: Dark" in response.text


def test_theme_mode_route_sets_cookie_and_returns_fragment() -> None:
    with TestClient(create_app()) as client:
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
    with TestClient(create_app()) as client:
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
    with TestClient(create_app(), follow_redirects=False) as client:
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
    with TestClient(create_app(), follow_redirects=False) as client:
        home_page = client.get("/")

        response = client.post(
            "/partials/theme-mode",
            data=csrf_data(home_page, {"theme_mode": "dark", "return_to": return_to}),
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert response.cookies["theme_mode"] == "dark"


def test_theme_mode_route_normalises_unsafe_htmx_return_to() -> None:
    with TestClient(create_app()) as client:
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
    with TestClient(create_app(), raise_server_exceptions=False) as client:
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
    with TestClient(create_app()) as client:
        response = client.post(
            "/partials/theme-mode",
            data={"theme_mode": "dark", "return_to": "/"},
            headers={"HX-Request": "true"},
        )

    assert response.status_code == 403
    assert "Invalid CSRF token." in response.text
    assert "theme_mode" not in response.cookies


def test_theme_mode_route_accepts_csrf_header() -> None:
    with TestClient(create_app()) as client:
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
    with TestClient(create_app()) as token_client:
        home_page = token_client.get("/")

    with TestClient(create_app()) as client:
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
            app_config=replace(
                build_test_app_config(
                    tmp_path,
                    modules=(
                        "identity_override_app",
                        "wevra.web",
                        "wevra.db",
                        "wevra.auth",
                    ),
                ),
                database_url=SQLITE_MEMORY_DATABASE_URL,
            ),
        )
    )

    with TestClient(web_app) as client:
        response = client.get("/account/login")

    assert response.status_code == 200
    assert "Overridden login" in response.text
    assert 'autocomplete="email"' not in response.text


def test_create_app_applies_configured_template_cache_options() -> None:
    app = create_app()
    with TestClient(app):
        renderer = app.state.renderer

    assert renderer.auto_reload is True
    assert renderer.cache_size == 0
    assert renderer.environment.auto_reload is True
