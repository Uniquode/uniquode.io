import asyncio
import inspect
import json
import logging
import os
import re
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
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

import auth_ext.sessions as identity_users
import uniquode.asgi as asgi_module
import uniquode.environment as environment_module
import uniquode.migrate as migrate_module
import uniquode.runserver as runserver_module
from auth_ext import (
    ERROR_ALREADY_EXISTS,
    ERROR_IDENTITY_CHANGED,
    ERROR_INACTIVE_USER,
    ERROR_INVALID_EMAIL,
    ERROR_INVALID_PASSWORD,
    ERROR_INVALID_TOKEN,
)
from auth_ext.bootstrap import (
    InitialAdminCredentials,
    bootstrap_initial_admin,
)
from auth_ext.models import (
    AccessToken,
    Base,
    InitialAdminBootstrap,
    OAuthAccount,
    User,
)
from auth_ext.models import (
    metadata as auth_ext_metadata,
)
from auth_ext.options import IdentityOptions
from auth_ext.schemas import UserCreate
from auth_ext.sessions import (
    create_authentication_backend,
    create_database_strategy,
    create_user_manager,
    require_anonymous_user,
    require_current_user,
)
from uniquode.app import create_app
from uniquode.asgi import app
from uniquode.configuration import ConfigurationError
from uniquode.environment import (
    ENV_ACCOUNT_CREATION_POLICY,
    ENV_ADVANCED_AUTH,
    ENV_ALEMBIC_CONFIG,
    ENV_APP_ENV,
    ENV_APP_NAME,
    ENV_APP_RELOAD,
    ENV_CSRF_SECRET,
    ENV_CSRF_SECURE,
    ENV_DATABASE_URL,
    ENV_MIGRATIONS_ROOT,
    ENV_OAUTH_LINKING,
    ENV_RESET_SECRET,
    ENV_SESSION_COOKIE,
    ENV_SESSION_LIFETIME,
    ENV_SESSION_SECURE,
    ENV_STATIC_ROOT,
    ENV_STATIC_URL,
    ENV_TEMPLATE_ROOT,
    ENV_VERIFICATION_SECRET,
    load_environment,
)
from uniquode.migration_metadata import ENABLED_MODEL_PACKAGES, load_model_metadata
from uniquode.models import metadata as uniquode_metadata
from uniquode.persistence import (
    Database,
    close_database,
    create_database,
    create_database_engine,
    create_session_factory,
    is_supported_database_url,
    session_scope,
    sqlite_database_path,
)
from uniquode.routes.health import health
from uniquode.runserver import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_RELOAD,
    RELOAD_ENV_VAR,
    build_parser,
    env_requests_reload,
    runtime_project_root,
)
from uniquode.settings import SQLITE_MEMORY_DATABASE_URL, Settings, load_settings
from uniquode.web.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_FIELD_NAME,
    CSRF_HEADER_NAME,
    CsrfProtector,
)
from uniquode.web.errors import EmptyBodyResponseException
from uniquode.web.renderer import TemplateRenderer
from uniquode.web.route_contract import _normalise_path_prefix

CSRF_INPUT_PATTERN = re.compile(
    rf'<input[^>]+name="{CSRF_FIELD_NAME}"[^>]+value="([^"]+)"'
)


def sqlite_file_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.resolve().as_posix()}"


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


def test_runserver_project_script_is_defined() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"

    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)

    assert data["project"]["scripts"]["runserver"] == "uniquode.runserver:main"
    assert data["project"]["scripts"]["validate"] == "uniquode.validate:main"
    assert data["project"]["scripts"]["migrate"] == "uniquode.migrate:main"


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
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)

    exit_code = migrate_module.main(["upgrade"])

    assert exit_code == 0
    assert calls == [
        (
            "upgrade",
            "head",
            sqlite_file_url(tmp_path / "uniquode.sqlite3"),
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


def test_migrate_database_url_override_preempts_blank_environment_value(
    tmp_path,
    monkeypatch,
) -> None:
    calls: list[tuple[str, str | None]] = []

    def record_current(config) -> None:
        calls.append(("current", config.get_main_option("sqlalchemy.url")))

    monkeypatch.setattr(migrate_module.command, "current", record_current)
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
    monkeypatch.setattr(migrate_module, "runtime_project_root", lambda: tmp_path)

    exit_code = migrate_module.main(argv)

    assert exit_code == 0
    assert calls == [
        (
            command_name,
            revision,
            sqlite_file_url(tmp_path / "uniquode.sqlite3"),
        )
    ]


def test_migrate_upgrade_initialises_empty_sqlite_database(tmp_path) -> None:
    database_path = tmp_path / "dev.sqlite3"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"

    exit_code = migrate_module.main(["--database-url", database_url, "upgrade"])

    assert exit_code == 0
    assert database_path.is_file()

    settings = Settings(database_url=database_url)
    engine = create_database_engine(settings)

    async def assert_tables() -> None:
        async with engine.begin() as connection:
            table_names = await connection.run_sync(
                lambda sync_connection: sqlalchemy_inspect(
                    sync_connection
                ).get_table_names()
            )

        assert "alembic_version" in table_names
        assert "identity_user" in table_names
        assert "identity_access_token" in table_names
        assert "identity_oauth_account" in table_names

    try:
        asyncio.run(assert_tables())
    finally:
        asyncio.run(close_database(engine))


def test_runserver_parser_uses_defaults() -> None:
    args = build_parser().parse_args([])

    assert args.host == DEFAULT_HOST
    assert args.port == DEFAULT_PORT
    assert args.reload is None
    assert RELOAD_ENV_VAR == "APP_RELOAD"


def test_runserver_loads_dotenv_from_runtime_project_root(monkeypatch) -> None:
    observed: dict[str, object] = {}

    class FakeEnv:
        def get(self, name: str, default: str | None = None) -> str | None:
            observed["reload_env_name"] = name
            return default

    def fake_load_environment(**kwargs: object) -> FakeEnv:
        observed.update(kwargs)
        return FakeEnv()

    def fake_uvicorn_run(*_args: object, **kwargs: object) -> None:
        observed["uvicorn_kwargs"] = kwargs

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(runserver_module.uvicorn, "run", fake_uvicorn_run)

    runserver_module.main([])

    assert observed["project_root"] == runtime_project_root()
    assert observed["reload_env_name"] == ENV_APP_RELOAD
    assert observed["uvicorn_kwargs"] == {
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "reload": DEFAULT_RELOAD,
    }


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

    static_routes = [r for r in web_app.routes if getattr(r, "name", None) == "static"]
    assert len(static_routes) == 1

    static_route = static_routes[0]
    assert static_route.path == "/assets"

    static_app = static_route.app
    assert isinstance(static_app, StaticFiles)
    assert Path(static_app.directory) == settings.static_root


def test_missing_static_asset_does_not_render_html_error_page() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/static/missing.css")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/plain")
    assert "<!doctype html>" not in response.text.lower()
    assert response.text == "Not Found"


def test_settings_resolve_default_roots_from_project_root(tmp_path) -> None:
    settings = Settings(project_root=tmp_path)

    assert settings.database_url == (
        f"sqlite+aiosqlite:///{(tmp_path / 'uniquode.sqlite3').resolve().as_posix()}"
    )
    assert settings.template_root == (tmp_path / "src/templates").resolve()
    assert settings.static_root == (tmp_path / "src/static").resolve()
    assert settings.migrations_root == (tmp_path / "src/uniquode/migrations").resolve()
    assert settings.alembic_config == (tmp_path / "alembic.ini").resolve()


def test_settings_default_database_url_uses_async_sqlalchemy_driver() -> None:
    assert Settings().database_url.endswith("/uniquode.sqlite3")
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
        database_url="sqlite+aiosqlite:///uniquode.sqlite3?mode=ro#fragment",
    )

    assert settings.database_url == (
        f"sqlite+aiosqlite:///"
        f"{(tmp_path / 'uniquode.sqlite3').resolve().as_posix()}?mode=ro#fragment"
    )


def test_load_settings_uses_environment_values(tmp_path) -> None:
    database_url = "postgresql+asyncpg://user:password@db.example/app"
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
            ENV_SESSION_LIFETIME: "3600",
            ENV_OAUTH_LINKING: "on",
            ENV_ADVANCED_AUTH: "1",
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
    assert settings.identity_options.session_lifetime_seconds == 3600
    assert settings.identity_options.reset_password_token_secret == "reset-secret"
    assert settings.identity_options.verification_token_secret == "verification-secret"
    assert settings.identity_options.oauth_account_linking_enabled is True
    assert settings.identity_options.advanced_authentication_enabled is True
    assert settings.static_mount_path == "/assets"


def test_load_settings_reads_local_dotenv(tmp_path) -> None:
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
        (ENV_SESSION_SECURE, "SESSION_SECURE must not be blank"),
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
    assert sqlite_database_path("sqlite+aiosqlite:///uniquode.sqlite3?mode=ro") == (
        Path("uniquode.sqlite3")
    )
    assert sqlite_database_path(
        "sqlite+aiosqlite:///uniquode.sqlite3#fragment"
    ) == Path("uniquode.sqlite3")


def test_settings_include_identity_options() -> None:
    settings = Settings()
    options = settings.identity_options

    assert settings.csrf_token_secret
    assert settings.csrf_cookie_secure is False
    assert settings.csrf_token_secret_configured is False
    assert options.account_creation_policy == "admin-created"
    assert options.session_cookie_name == "uniquode_session"
    assert options.session_cookie_secure is True
    assert options.session_lifetime_seconds == 2_592_000
    assert options.token_secrets_configured is False
    assert options.integration_enabled("oauth-account-linking") is False
    assert options.integration_enabled("advanced-authentication") is False


def test_identity_options_accept_public_signup_policy() -> None:
    options = IdentityOptions(account_creation_policy="public-signup")

    assert options.account_creation_policy == "public-signup"


def test_identity_options_reject_invalid_account_creation_policy() -> None:
    with pytest.raises(ConfigurationError, match="Account creation policy"):
        IdentityOptions(account_creation_policy="public_signup")  # type: ignore[arg-type]


def test_load_settings_reads_account_creation_policy_env(tmp_path) -> None:
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
    caplog.set_level(logging.INFO, logger="uniquode.settings")

    settings = Settings()

    assert settings.csrf_token_secret_configured is False
    assert "Generated startup-local CSRF token secret." in caplog.text


def test_identity_options_reject_invalid_session_lifetime() -> None:
    with pytest.raises(
        ConfigurationError,
        match="Session lifetime must be a positive number of seconds",
    ):
        IdentityOptions(session_lifetime_seconds=0)


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
        ),
    )

    assert settings.identity_options.token_secrets_configured is True
    assert settings.csrf_token_secret_configured is True
    assert settings.csrf_cookie_secure is True


def test_non_local_settings_require_secure_session_cookies() -> None:
    identity_options = IdentityOptions(
        session_cookie_secure=False,
        reset_password_token_secret="production-reset-secret",
        verification_token_secret="production-verification-secret",
    )

    with pytest.raises(
        ConfigurationError,
        match="Non-local deployments must use secure session cookies",
    ):
        Settings(
            deployment_environment="production",
            csrf_token_secret="production-csrf-secret",
            identity_options=identity_options,
        )


def test_local_settings_allow_insecure_session_cookies() -> None:
    settings = Settings(
        identity_options=IdentityOptions(session_cookie_secure=False),
    )

    assert settings.deployment_environment == "local"
    assert settings.identity_options.session_cookie_secure is False


def test_load_settings_rejects_insecure_non_local_session_cookie_env(
    tmp_path,
) -> None:
    with pytest.raises(
        ConfigurationError,
        match="Non-local deployments must use secure session cookies",
    ):
        load_settings(
            environ={
                ENV_APP_ENV: "production",
                ENV_CSRF_SECRET: "production-csrf-secret",
                ENV_RESET_SECRET: "production-reset-secret",
                ENV_VERIFICATION_SECRET: "production-verification-secret",
                ENV_SESSION_SECURE: "false",
            },
            project_root=tmp_path,
            read_dotenv=False,
        )


def test_non_local_settings_require_configured_csrf_token_secret() -> None:
    identity_options = IdentityOptions(
        reset_password_token_secret="production-reset-secret",
        verification_token_secret="production-verification-secret",
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
    options = IdentityOptions(
        oauth_account_linking_enabled=True,
        advanced_authentication_enabled=True,
    )

    assert options.integration_enabled("oauth-account-linking") is True
    assert options.integration_enabled("advanced-authentication") is True


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
    oauth_columns = set(OAuthAccount.__table__.columns.keys())
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
        "oauth_name",
        "access_token",
        "expires_at",
        "refresh_token",
        "account_id",
        "account_email",
        "user_id",
    }.issubset(oauth_columns)
    assert {"token", "created_at", "user_id"}.issubset(access_token_columns)
    assert User.__tablename__ == "identity_user"
    assert OAuthAccount.__tablename__ == "identity_oauth_account"
    assert AccessToken.__tablename__ == "identity_access_token"


def test_oauth_account_model_links_to_local_user() -> None:
    oauth_foreign_keys = OAuthAccount.__table__.columns["user_id"].foreign_keys
    access_token_foreign_keys = AccessToken.__table__.columns["user_id"].foreign_keys

    assert {str(foreign_key.column) for foreign_key in oauth_foreign_keys} == {
        "identity_user.id"
    }
    assert {str(foreign_key.column) for foreign_key in access_token_foreign_keys} == {
        "identity_user.id"
    }
    assert User.oauth_accounts.property.mapper.class_ is OAuthAccount


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

        assert "identity_user" in table_names
        assert "identity_oauth_account" in table_names
        assert "identity_access_token" in table_names

    try:
        asyncio.run(assert_tables())
    finally:
        asyncio.run(close_database(engine))


def test_auth_ext_models_export_migration_metadata() -> None:
    assert auth_ext_metadata is Base.metadata


def test_enabled_model_packages_are_explicit_for_current_application() -> None:
    assert ENABLED_MODEL_PACKAGES == ("uniquode.models", "auth_ext.models")


def test_enabled_model_packages_load_migration_metadata_in_order() -> None:
    metadata_values = load_model_metadata()

    assert len(metadata_values) == len(ENABLED_MODEL_PACKAGES)
    assert all(isinstance(value, MetaData) for value in metadata_values)
    assert metadata_values[0] is uniquode_metadata
    assert metadata_values[1] is auth_ext_metadata


def test_model_metadata_loader_with_no_packages_returns_empty_tuple() -> None:
    assert load_model_metadata(()) == ()


def test_model_metadata_loader_rejects_packages_without_metadata() -> None:
    with pytest.raises(
        RuntimeError,
        match=r"dummy_no_metadata.*Module origin:.*Available attributes:",
    ):
        load_model_metadata(("dummy_no_metadata",))


def test_model_metadata_loader_rejects_non_metadata_attribute() -> None:
    with pytest.raises(
        RuntimeError,
        match=r"dummy_invalid_metadata.*Module origin:.*Available attributes:",
    ):
        load_model_metadata(("dummy_invalid_metadata",))


def test_model_metadata_loader_reports_missing_configured_package() -> None:
    with pytest.raises(RuntimeError, match="could not be imported"):
        load_model_metadata(("missing_model_package",))


def test_model_metadata_loader_preserves_nested_import_failures() -> None:
    with pytest.raises(ModuleNotFoundError, match="missing_dependency"):
        load_model_metadata(("dummy_missing_dependency",))


def test_identity_authentication_backend_uses_http_only_session_cookie() -> None:
    options = IdentityOptions(
        session_cookie_name="u_test_session",
        session_cookie_secure=True,
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


def test_authentication_ceremony_finalisation_creates_active_user_session() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(session_cookie_secure=False),
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
            identity_options=IdentityOptions(session_cookie_secure=False),
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
            identity_options=IdentityOptions(session_cookie_secure=False),
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
) -> None:
    async def seed_user() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_scope(web_app.state.database.session_factory) as session:
            manager = create_user_manager(
                session, web_app.state.settings.identity_options
            )
            await manager.create(
                UserCreate(
                    email=email,
                    password=password,
                    is_active=is_active,
                    is_verified=is_verified,
                ),
                safe=False,
            )

    asyncio.run(seed_user())


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
            "path": "/logout",
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
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(session_cookie_secure=False),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)

        login_page = client.get("/login")
        assert login_page.status_code == 200
        assert "Sign in" in login_page.text
        assert CSRF_COOKIE_NAME in login_page.cookies
        assert f'name="{CSRF_FIELD_NAME}"' in login_page.text

        login_response = client.post(
            "/login",
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

        logout_page = client.get("/logout")
        assert logout_page.status_code == 200
        assert "End the current browser session." in logout_page.text

        logout_response = client.post("/logout", data=csrf_data(logout_page))
        assert logout_response.status_code == 303
        assert logout_response.headers["location"] == "/"
        assert "Max-Age=0" in logout_response.headers["set-cookie"]

        logged_out_user = client.get("/api/identity/current-user")
        assert logged_out_user.json() == {"authenticated": False}
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_is_not_exposed_by_default() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(session_cookie_secure=False),
        )
    )

    try:
        client = TestClient(web_app, follow_redirects=False)

        assert client.get("/signup").status_code == 404
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_public_signup_route_rechecks_policy_when_mounted() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
                session_cookie_secure=False,
            ),
        )
    )
    web_app.state.identity_options = IdentityOptions(session_cookie_secure=False)

    try:
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/login")

        assert client.get("/signup").status_code == 404
        submit_response = client.post(
            "/signup",
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
                session_cookie_secure=False,
            ),
        )
    )

    async def create_schema() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    try:
        asyncio.run(create_schema())
        client = TestClient(web_app, follow_redirects=False)
        signup_page = client.get("/signup")

        assert signup_page.status_code == 200
        assert "Create account" in signup_page.text

        signup_response = client.post(
            "/signup",
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

        login_page = client.get("/login")
        login_response = client.post(
            "/login",
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
                session_cookie_secure=False,
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
                session_cookie_secure=False,
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


def test_public_signup_rejects_malformed_email_before_user_creation() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(
                account_creation_policy="public-signup",
                session_cookie_secure=False,
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
                session_cookie_secure=False,
            ),
        )
    )

    async def create_schema() -> None:
        async with web_app.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    try:
        asyncio.run(create_schema())
        client = TestClient(web_app, follow_redirects=False)
        signup_page = client.get("/signup")

        response = client.post(
            "/signup",
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
                session_cookie_secure=False,
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
            identity_options=IdentityOptions(session_cookie_secure=False),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)

        response = client.post(
            "/login",
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
            identity_options=IdentityOptions(session_cookie_secure=False),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)

        login_page = client.get("/login", params={"return_to": return_to})
        assert login_page.status_code == 200
        assert 'name="return_to" type="hidden" value="/account"' in login_page.text
        assert return_to not in login_page.text

        login_response = client.post(
            "/login",
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
            identity_options=IdentityOptions(session_cookie_secure=False),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/login")

        response = client.post(
            "/login",
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
                session_cookie_secure=False,
            ),
        )
    )

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/login")

        response = client.post(
            "/login",
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
        assert str(web_app.url_path_for("identity:signup")) in response.text
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_identity_login_rejects_inactive_user() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(session_cookie_secure=False),
        )
    )

    try:
        seed_identity_user(web_app, is_active=False)
        client = TestClient(web_app, follow_redirects=False)
        login_page = client.get("/login")

        response = client.post(
            "/login",
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
            identity_options=IdentityOptions(session_cookie_secure=False),
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
        login_page = client.get("/login")
        login_response = client.post(
            "/login",
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


def test_identity_dependency_helpers_handle_required_and_anonymous_users() -> None:
    web_app = create_app(
        Settings(
            database_url=SQLITE_MEMORY_DATABASE_URL,
            identity_options=IdentityOptions(session_cookie_secure=False),
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

        login_page = client.get("/login")
        client.post(
            "/login",
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
            identity_options=IdentityOptions(session_cookie_secure=False),
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
        login_page = client.get("/login")
        login_response = client.post(
            "/login",
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
        reset_page = client.get("/password/reset")

        response = client.post(
            "/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )

        assert response.status_code == 200
        assert delivery.reset_tokens
        assert delivery.reset_tokens[0][0] == "person@example.com"

        confirm_response = client.post(
            "/password/reset/confirm",
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
        reset_page = client.get("/password/reset")

        response = client.post(
            "/password/reset/confirm",
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
        reset_page = client.get("/password/reset")

        response = client.post(
            "/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )
        assert response.status_code == 200
        assert delivery.reset_tokens

        confirm_response = client.post(
            "/password/reset/confirm",
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
        reset_page = client.get("/password/reset")

        response = client.post(
            "/password/reset",
            data=csrf_data(reset_page, {"email": "person@example.com"}),
        )

        assert response.status_code == 200
        assert "If the account exists, a reset link has been queued." in response.text
        assert delivery.reset_tokens == []
    finally:
        asyncio.run(close_database(web_app.state.database))


def test_verification_route_uses_delivery_hook() -> None:
    web_app = create_app(Settings(database_url=SQLITE_MEMORY_DATABASE_URL))
    delivery = CaptureIdentityDelivery()
    web_app.state.identity_delivery = delivery

    try:
        seed_identity_user(web_app)
        client = TestClient(web_app, follow_redirects=False)
        verify_page = client.get("/verify")

        response = client.post(
            "/verify", data=csrf_data(verify_page, {"email": "person@example.com"})
        )

        assert response.status_code == 200
        assert delivery.verification_tokens
        assert delivery.verification_tokens[0][0] == "person@example.com"

        confirm_response = client.post(
            "/verify/confirm",
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
        verify_page = client.get("/verify")

        response = client.post(
            "/verify", data=csrf_data(verify_page, {"email": "person@example.com"})
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
            "/verify/confirm",
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
        verify_page = client.get("/verify")

        response = client.post(
            "/verify", data=csrf_data(verify_page, {"email": "person@example.com"})
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
            "/verify/confirm",
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
        verify_page = client.get("/verify")

        response = client.post(
            "/verify", data=csrf_data(verify_page, {"email": "person@example.com"})
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
        verify_page = client.get("/verify")
        verification_result = asyncio.run(
            identity_users.verify_user(
                Request({"type": "http", "app": web_app}),
                "invalid",
            )
        )

        assert verification_result.is_failure() is True
        assert verification_result.error_type == ERROR_INVALID_TOKEN

        response = client.post(
            "/verify/confirm",
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

    response = client.get("/api/public/theme")

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


def test_base_layout_updates_root_theme_from_htmx_event() -> None:
    layout_template = (
        Path(__file__).resolve().parents[1] / "src/templates/layouts/page.html"
    ).read_text()

    assert 'addEventListener("theme-mode-changed"' in layout_template
    assert 'document.documentElement.removeAttribute("data-theme")' in layout_template
    assert (
        'document.documentElement.setAttribute("data-theme", themeMode)'
        in layout_template
    )


def test_template_renderer_falls_back_when_route_name_is_missing() -> None:
    renderer = TemplateRenderer(Path(__file__).resolve().parents[1] / "src/templates")
    request = Request({"type": "http", "headers": [], "method": "GET", "path": "/"})

    response = renderer.render_page(
        "components/theme_selector.html",
        request,
        {
            "theme_mode": "auto",
            "theme_label": "Auto",
            "theme_attribute": "",
            "theme_next_mode": "light",
            "theme_icon_name": "computer",
            "theme_update_path": "/partials/theme-mode",
        },
    )

    assert response.status_code == 200
    assert b'id="theme-selector"' in response.body


def test_template_renderer_rejects_internal_context_overrides() -> None:
    renderer = TemplateRenderer(
        Path(__file__).resolve().parents[1] / "src/templates",
        csrf=CsrfProtector("test-secret"),
    )
    request = Request({"type": "http", "headers": [], "method": "GET", "path": "/"})

    with pytest.raises(ValueError, match="csrf_token"):
        renderer.render_page(
            "components/theme_selector.html",
            request,
            {
                "theme_mode": "auto",
                "theme_label": "Auto",
                "theme_attribute": "",
                "theme_next_mode": "light",
                "theme_icon_name": "computer",
                "theme_update_path": "/partials/theme-mode",
                "csrf_token": "caller-controlled",
            },
        )


def test_project_stylesheet_defines_semantic_theme_tokens() -> None:
    stylesheet = (
        Path(__file__).resolve().parents[1] / "src/static/styles/app.css"
    ).read_text()

    assert "--u-colour-page-bg" in stylesheet
    assert "--u-colour-surface" in stylesheet
    assert "--u-colour-text" in stylesheet
    assert "--u-colour-accent" in stylesheet
    assert 'html[data-theme="light"]' in stylesheet
    assert 'html[data-theme="dark"]' in stylesheet
    assert "@media (prefers-color-scheme: dark)" in stylesheet


def test_base_layout_uses_theme_tokens_without_template_colour_branching() -> None:
    layout_template = (
        Path(__file__).resolve().parents[1] / "src/templates/layouts/page.html"
    ).read_text()

    assert "{% if theme_attribute %} data-theme=" in layout_template
    assert "#0f766e" not in layout_template
    assert "#f7f9f8" not in layout_template
    assert "#eef4f2" not in layout_template
