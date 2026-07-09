import ast
import importlib
import inspect
import json
import re
import tomllib
from dataclasses import replace
from pathlib import Path
from textwrap import dedent
from typing import cast

import pytest
import wybra.tools.runserver as runserver_module
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.routing import Mount
from wybra import get_site
from wybra.assets import StaticAssetCapability
from wybra.auth import AuthCapability
from wybra.auth.models import (
    User,
)
from wybra.config import load_configured_settings
from wybra.core.asgi import load_asgi_app
from wybra.core.composition import (
    AppConfig,
    AssetOptions,
    RouteOptions,
    TemplateOptions,
)
from wybra.core.exceptions import ConfigurationError
from wybra.core.routes.contracts import _normalise_path_prefix
from wybra.db import DatabaseCapability
from wybra.db.urls import SQLITE_MEMORY_DATABASE_URL
from wybra.forms import (
    CSRF_FIELD_NAME,
    CSRF_HEADER_NAME,
)
from wybra.template import DefaultTemplateCapability, TemplateCapability
from wybra.tools.project import (
    runtime_project_root,
)
from wybra.tools.runserver import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_RELOAD,
    env_requests_reload,
)

from config_support import (
    AUTH_WEB_MODULES,
    FULL_APP_MODULES,
    PUBLIC_WEB_MODULES,
    TEST_ROUTE_PREFIXES,
    WEB_RUNTIME_MODULES,
)
from uniquode_io.app import create_app
from uniquode_io.routes import health
from uniquode_io.settings import Settings

CSRF_INPUT_PATTERN = re.compile(
    rf'<input[^>]+name="{CSRF_FIELD_NAME}"[^>]+value="([^"]+)"'
)
RUNSERVER_RELOAD_ENV = "APP_RELOAD"


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


def write_app_config(
    path: Path,
    *,
    modules: tuple[str, ...] = FULL_APP_MODULES,
    route_prefixes: dict[str, dict[str, str]] | None = None,
    static_url_path: str = "/static/",
    static_asset_root: str = "static",
    database_backend: str = "sqlite",
    database: str = "app.sqlite3",
    auth_options: dict[str, object] | None = None,
    name: str | None = None,
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
    name_config = "" if name is None else f"name = {json.dumps(name)}"
    structured_database_config = f"""
        [app.database]
        backend = {json.dumps(database_backend)}
        database = {json.dumps(database)}
        """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""
        [app]
        {name_config}
        modules = {json.dumps(list(modules))}

        {structured_database_config}

        [app.routes]
        {route_config}

        [app.runserver]
        asgi_app = "uniquode_io.asgi:app"
        reload_env = "APP_RELOAD"

        [app.templates]
        auto_reload = true
        cache_size = 0

        [app.assets]
        url_path = {json.dumps(static_url_path)}
        root = {json.dumps(static_asset_root)}

        [wybra.sessions]
        storage_backend = "memory"

        [wybra.messages]
        storage_backend = "session"

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


@pytest.fixture(autouse=True)
def use_generated_app_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_CONFIG", str(write_app_config(tmp_path / "app.toml")))


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


def test_write_app_config_writes_memory_database_as_structured_sqlite(
    tmp_path: Path,
) -> None:
    config_path = write_app_config(
        tmp_path / "app.toml",
        database=":memory:",
    )

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    assert "database_url" not in data["app"]
    assert data["app"]["database"] == {
        "backend": "sqlite",
        "database": ":memory:",
    }


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
        assets=AssetOptions(url_path="/static/", root=Path("static")),
        auth={
            "session_cookie_name": "test_session",
            "session_cookie_force_secure": False,
        }
        if "wybra.auth" in modules
        else {},
    )


def test_asgi_app_imports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_CONFIG", str(write_app_config(tmp_path / "app.toml")))

    asgi_module = importlib.import_module("uniquode_io.asgi")

    assert isinstance(asgi_module.app, FastAPI)


def test_asgi_loader_reports_configuration_errors_without_traceback(
    capsys,
) -> None:
    def raise_configuration_error():
        raise ConfigurationError("APP_ENV must be local, staging, or production.")

    with pytest.raises(SystemExit) as excinfo:
        load_asgi_app(raise_configuration_error)

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


def test_create_app_requires_config_source_with_explicit_settings() -> None:
    with pytest.raises(
        ValueError,
        match="config_source is required when explicit settings are passed",
    ):
        create_app(settings=Settings())


def test_create_app_uses_wybra_lifespan_startup_for_configured_routes() -> None:
    with TestClient(create_app()) as client:
        login_response = client.get("/account/login")
        static_response = client.get("/static/styles/app.css")
        health_response = client.get("/health")

    assert login_response.status_code == 200
    assert static_response.status_code == 200
    assert health_response.status_code == 200


def test_baseline_route_handlers_are_async() -> None:
    assert inspect.iscoroutinefunction(health)


def test_app_project_does_not_redeclare_wybra_operator_scripts() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"

    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)

    scripts = data["project"].get("scripts", {})
    wybra_operator_scripts = {
        "identitymgr",
        "migrate",
        "routes",
        "runserver",
        "validate",
        "wybra-authmgr",
        "wybra-identitymgr",
        "wybra-migrate",
        "wybra-routes",
        "wybra-runserver",
        "wybra-validate",
    }

    assert scripts.keys().isdisjoint(wybra_operator_scripts)


def test_app_runtime_does_not_import_wybra_owned_configuration_details() -> None:
    app_root = Path(__file__).resolve().parents[1] / "src/uniquode_io"
    forbidden_imports = {
        "wybra.auth.configuration",
        "wybra.auth.settings",
        "wybra.db.migrate",
        "wybra.db.surfaces",
    }
    imported_modules = {
        module for path in app_root.rglob("*.py") for module in _imported_modules(path)
    }

    assert imported_modules.isdisjoint(forbidden_imports)


def test_runserver_delegates_default_arguments_to_uvicorn(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_load_environment(**kwargs: object) -> dict[str, str]:
        observed.update(kwargs)
        return {}

    def fake_run_uvicorn_command(
        args: list[str], *, logging_config: object | None = None
    ) -> None:
        observed["uvicorn_args"] = args
        observed["logging_config"] = logging_config

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(
        runserver_module, "run_uvicorn_command", fake_run_uvicorn_command, raising=False
    )

    runserver_module.main([])

    assert observed["project_root"] == runtime_project_root()
    assert observed["uvicorn_args"] == [
        "uniquode_io.asgi:app",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(DEFAULT_PORT),
    ]


def test_runserver_loads_dotenv_from_runtime_project_root(monkeypatch) -> None:
    observed: dict[str, object] = {}

    class FakeEnv:
        def get(self, name: str, default: str | None = None) -> str | None:
            observed["reload_env_name"] = name
            return default

    def fake_load_environment(**kwargs: object) -> FakeEnv:
        observed.update(kwargs)
        return FakeEnv()

    def fake_run_uvicorn_command(
        args: list[str], *, logging_config: object | None = None
    ) -> None:
        observed["uvicorn_args"] = args
        observed["logging_config"] = logging_config

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(
        runserver_module, "run_uvicorn_command", fake_run_uvicorn_command, raising=False
    )

    runserver_module.main([])

    assert observed["project_root"] == runtime_project_root()
    assert observed["reload_env_name"] == RUNSERVER_RELOAD_ENV
    assert observed["uvicorn_args"] == [
        "uniquode_io.asgi:app",
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
        return {RUNSERVER_RELOAD_ENV: "on"}

    def fake_run_uvicorn_command(
        args: list[str], *, logging_config: object | None = None
    ) -> None:
        observed["uvicorn_args"] = args
        observed["logging_config"] = logging_config

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(
        runserver_module, "run_uvicorn_command", fake_run_uvicorn_command, raising=False
    )

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
        "uniquode_io.asgi:app",
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
        return {RUNSERVER_RELOAD_ENV: "on"}

    def fake_run_uvicorn_command(
        args: list[str], *, logging_config: object | None = None
    ) -> None:
        observed["uvicorn_args"] = args
        observed["logging_config"] = logging_config

    monkeypatch.setattr(runserver_module, "load_environment", fake_load_environment)
    monkeypatch.setattr(
        runserver_module, "run_uvicorn_command", fake_run_uvicorn_command
    )

    runserver_module.main(["--no-reload"])

    assert observed["uvicorn_args"] == [
        "uniquode_io.asgi:app",
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
    runserver_module.reject_extra_app_target(
        ["uniquode_io.asgi:app"],
        app_target="uniquode_io.asgi:app",
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
    runserver_module.reject_extra_app_target(
        [option_value],
        app_target="uniquode_io.asgi:app",
    )


def test_create_app_mounts_configurable_static_files(tmp_path: Path) -> None:
    static_root = tmp_path / "src/test-static"
    static_root.mkdir(parents=True)
    app_config = replace(
        build_test_app_config(
            tmp_path,
            modules=WEB_RUNTIME_MODULES,
        ),
        assets=AssetOptions(
            url_path="/assets/",
            root=Path("src/test-static"),
        ),
    )
    web_app = create_app(config_source=app_config)

    with TestClient(web_app):
        static_routes = [
            route
            for route in web_app.routes
            if getattr(route, "name", None) == "static"
        ]
    assert len(static_routes) == 1

    static_route = static_routes[0]
    assert isinstance(static_route, Mount)
    assert static_route.path == "/assets"

    with TestClient(web_app) as client:
        site = get_site(web_app)
        capability = site.require_capability(StaticAssetCapability)
        response = client.get(capability.url("styles/app.css"))

    assert capability.url_path == "/assets"
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_create_app_serves_static_files_from_configured_modules() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/static/styles/app.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert "--web-core-colour-page-bg" in response.text


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
        config_source=build_test_app_config(
            tmp_path,
            modules=("prefixed_route_app", *WEB_RUNTIME_MODULES),
            route_prefixes={"prefixed_route_app": {"default": "/tools"}},
        ),
    )

    with TestClient(app) as client:
        assert client.get("/tools/ping").text == "prefixed"
        assert client.get("/ping").status_code == 404


def test_create_app_registers_routes_only_from_configured_modules(
    tmp_path: Path,
) -> None:
    app = create_app(
        config_source=build_test_app_config(
            tmp_path,
            modules=PUBLIC_WEB_MODULES,
        ),
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
        config_source=replace(
            build_test_app_config(
                tmp_path,
                modules=PUBLIC_WEB_MODULES,
            ),
            templates=TemplateOptions(
                auto_reload=True,
                cache_size=0,
                root=template_root,
            ),
        ),
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


def test_settings_defaults_to_app_owned_values() -> None:
    settings = Settings()

    assert settings.app_name == "uniquode"


def test_settings_rejects_blank_app_name() -> None:
    with pytest.raises(ConfigurationError, match=r"\[app\]\.name must not be blank"):
        Settings(name="   ")


def test_load_settings_reads_mapping_values() -> None:
    settings = Settings.load_settings({"name": "mapping-app"})

    assert settings.app_name == "mapping-app"


def test_load_configured_settings_reads_explicit_config_source(tmp_path) -> None:
    config_path = write_app_config(
        tmp_path / "app.toml",
        modules=("uniquode_io", "wybra.db", "wybra.auth"),
        static_url_path="/assets/",
        database="identity.sqlite3",
        name="file-app",
    )

    settings = load_configured_settings(
        Settings,
        config_source=str(config_path),
    )

    assert settings.app_name == "file-app"


def test_load_settings_uses_app_config_environment_override(tmp_path) -> None:
    config_path = write_app_config(
        tmp_path / "config" / "application.toml",
        modules=("uniquode_io",),
        static_url_path="/public-static/",
        name="override-file-app",
    )

    settings = load_configured_settings(
        Settings,
        config_source=str(config_path),
    )

    assert settings.app_name == "override-file-app"


def test_load_settings_rejects_missing_app_config_override(tmp_path) -> None:
    with pytest.raises(ConfigurationError, match="App config file does not exist"):
        load_configured_settings(
            Settings,
            config_source=str(tmp_path / "missing.toml"),
        )


def test_load_settings_uses_configured_app_name(tmp_path) -> None:
    config_path = write_app_config(tmp_path / "app.toml", name="configured-app")
    settings = load_configured_settings(
        Settings,
        config_source=str(config_path),
    )

    assert settings.app_name == "configured-app"


def test_load_settings_ignores_local_dotenv_for_stable_app_name(tmp_path) -> None:
    config_path = write_app_config(tmp_path / "app.toml")
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "APP_NAME=dotenv-app",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_configured_settings(
        Settings,
        config_source=str(config_path),
    )

    assert settings.app_name == "uniquode"


def test_explicit_settings_override_configured_app_name() -> None:
    settings = Settings(name="explicit-app")

    assert settings.app_name == "explicit-app"


def test_app_config_preserves_configured_auth_module(tmp_path: Path) -> None:
    app_config = AppConfig(
        config_path=(tmp_path / "app.toml").resolve(),
        project_root=tmp_path.resolve(),
        modules=FULL_APP_MODULES,
        routes=RouteOptions(prefixes={}),
        templates=TemplateOptions(auto_reload=True, cache_size=0),
        assets=AssetOptions(url_path="/static/", root=Path("static")),
        auth={},
    )

    assert app_config.modules == FULL_APP_MODULES


def test_create_app_configures_database_and_identity_boundaries() -> None:
    with TestClient(create_app()) as client:
        app = cast(FastAPI, client.app)
        site = get_site(app)
        database = site.require_capability(DatabaseCapability)
        auth = site.require_capability(AuthCapability)

        assert database is site.require_capability(DatabaseCapability)
        assert auth is site.require_capability(AuthCapability)
        assert callable(database.connection)
        assert callable(database.transaction)
        assert callable(auth.login_required)

    assert not hasattr(app.state, "database")
    assert not hasattr(app.state, "identity_options")


def test_create_app_without_explicit_settings_uses_configured_app_name(
    tmp_path,
) -> None:
    app_config = replace(
        build_test_app_config(
            tmp_path,
            modules=PUBLIC_WEB_MODULES,
        ),
        raw_config={"app": {"name": "configured-app"}},
    )
    web_app = create_app(config_source=app_config)

    with TestClient(web_app):
        assert web_app.title == "configured-app"


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
        response = client.get("/api/widgets/theme")

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


def test_earlier_application_module_can_override_wybra_auth_identity_template(
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
        config_source=replace(
            build_test_app_config(
                tmp_path,
                modules=("identity_override_app", *AUTH_WEB_MODULES),
            ),
            database_url=SQLITE_MEMORY_DATABASE_URL,
        ),
    )

    with TestClient(web_app) as client:
        response = client.get("/account/login")

    assert response.status_code == 200
    assert "Overridden login" in response.text
    assert 'autocomplete="email"' not in response.text


def test_create_app_applies_configured_template_cache_options() -> None:
    app = create_app()
    with TestClient(app):
        renderer = get_site(app).require_capability(TemplateCapability)

    assert isinstance(renderer, DefaultTemplateCapability)
    assert renderer.auto_reload is True
    assert renderer.cache_size == 0
    assert renderer.environment.auto_reload is True


def test_create_app_without_database_or_auth_modules_registers_no_capabilities(
    tmp_path: Path,
) -> None:
    web_app = create_app(
        config_source=build_test_app_config(
            tmp_path,
            modules=PUBLIC_WEB_MODULES,
        ),
    )

    with TestClient(web_app) as client:
        site = get_site(cast(FastAPI, client.app))

        assert not site.has_capability(DatabaseCapability)
        assert not site.has_capability(AuthCapability)


def test_configured_compatible_database_provider_is_not_replaced_by_wybra_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_root = tmp_path / "compatible_database_app"
    package_root.mkdir()
    (package_root / "__init__.py").write_text(
        "from wybra.db import DatabaseCapability\n\n"
        "class CompatibleDatabaseCapability:\n"
        "    def connection(self, name='default'):\n"
        "        raise NotImplementedError\n"
        "    def session(self, name='default'):\n"
        "        raise NotImplementedError\n"
        "    def transaction(self, name='default'):\n"
        "        raise NotImplementedError\n"
        "    async def close(self):\n"
        "        return None\n\n"
        "async def setup_site(site):\n"
        "    capability = CompatibleDatabaseCapability()\n"
        "    site.provide_capability(DatabaseCapability, capability)\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    web_app = create_app(
        config_source=build_test_app_config(
            tmp_path,
            modules=("compatible_database_app", *PUBLIC_WEB_MODULES),
        ),
    )

    with TestClient(web_app) as client:
        site = get_site(cast(FastAPI, client.app))

        assert type(site.require_capability(DatabaseCapability)).__name__ == (
            "CompatibleDatabaseCapability"
        )
