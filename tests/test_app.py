import inspect
import json
import tomllib
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.staticfiles import StaticFiles

from uniquode.app import create_app
from uniquode.asgi import app
from uniquode.routes.health import health
from uniquode.runserver import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_RELOAD,
    build_parser,
    env_requests_reload,
)
from uniquode.settings import Settings
from uniquode.validate import main as validate_main
from uniquode.web.errors import EmptyBodyResponseException
from uniquode.web.renderer import TemplateRenderer
from uniquode.web.route_contract import _normalise_path_prefix


def test_asgi_app_imports() -> None:
    assert isinstance(app, FastAPI)


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


def test_runserver_parser_uses_defaults() -> None:
    args = build_parser().parse_args([])

    assert args.host == DEFAULT_HOST
    assert args.port == DEFAULT_PORT
    assert args.reload is None


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

    assert settings.template_root == (tmp_path / "src/templates").resolve()
    assert settings.static_root == (tmp_path / "src/static").resolve()


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

    response = client.post(
        "/partials/theme-mode",
        data={"theme_mode": "light", "return_to": "/"},
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

    response = client.post(
        "/partials/theme-mode",
        data={"theme_mode": "neon", "return_to": "/"},
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

    response = client.post(
        "/partials/theme-mode",
        data={"theme_mode": "dark", "return_to": "/"},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert response.cookies["theme_mode"] == "dark"
    assert "HttpOnly" in response.headers["set-cookie"]


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


def test_validate_command_checks_web_foundation(capsys) -> None:
    exit_code = validate_main(["web"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "web: ok" in captured.out


def test_validate_command_unknown_target_raises_system_exit(capsys) -> None:
    with pytest.raises(
        SystemExit, match="Unknown validation target\\(s\\): foo"
    ) as excinfo:
        validate_main(["foo"])

    captured = capsys.readouterr()
    assert "foo" in str(excinfo.value)
    assert captured.out == ""
    assert captured.err == ""


def test_validate_command_accepts_normalisable_static_url_path(capsys) -> None:
    exit_code = validate_main(["web", "--static-url-path", "static"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "web: ok" in captured.out


def test_validate_command_rejects_blank_static_url_path(capsys) -> None:
    exit_code = validate_main(["web", "--static-url-path", "   "])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Static URL path must not be empty." in captured.out


def test_validate_command_reports_missing_templates(tmp_path, capsys) -> None:
    settings = Settings(
        template_root=tmp_path / "templates",
        static_root=tmp_path / "static",
    )
    settings.static_root.mkdir()

    exit_code = validate_main(
        [
            "web",
            "--template-root",
            str(settings.template_root),
            "--static-root",
            str(settings.static_root),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Missing template" in captured.out


def test_validate_command_reports_missing_theme_tokens(tmp_path, capsys) -> None:
    template_root = tmp_path / "templates"
    static_root = tmp_path / "static"
    (template_root / "public/pages").mkdir(parents=True)
    (template_root / "public/partials").mkdir(parents=True)
    (template_root / "layouts").mkdir(parents=True)
    (template_root / "components").mkdir(parents=True)
    (template_root / "errors").mkdir(parents=True)
    (static_root / "styles").mkdir(parents=True)

    source_root = Path(__file__).resolve().parents[1]
    template_paths = (
        "public/pages/home.html",
        "layouts/page.html",
        "components/theme_switcher.html",
        "components/theme_selector.html",
        "errors/base.html",
    )
    for template_path in template_paths:
        source = source_root / "src/templates" / template_path
        destination = template_root / template_path
        destination.write_text(source.read_text())

    (static_root / "styles/app.css").write_text(":root {}")

    exit_code = validate_main(
        [
            "web",
            "--template-root",
            str(template_root),
            "--static-root",
            str(static_root),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Missing theme token" in captured.out
    assert "Missing theme selector" in captured.out
