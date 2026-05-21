import inspect
import tomllib
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute

from uniquode.app import create_app
from uniquode.asgi import app
from uniquode.routes.health import health
from uniquode.runserver import (
    APP_TARGET,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_RELOAD,
    build_parser,
)
from uniquode.runserver import (
    main as runserver_main,
)


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


def test_runserver_main_uses_expected_uvicorn_defaults(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(app_target: str, **kwargs: object) -> None:
        captured["app_target"] = app_target
        captured["kwargs"] = kwargs

    monkeypatch.setattr("uniquode.runserver.uvicorn.run", fake_run)

    runserver_main([])

    assert captured["app_target"] == APP_TARGET
    assert captured["kwargs"] == {
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "reload": DEFAULT_RELOAD,
    }


def test_runserver_parser_uses_defaults() -> None:
    args = build_parser().parse_args([])

    assert args.host == DEFAULT_HOST
    assert args.port == DEFAULT_PORT
    assert args.reload is DEFAULT_RELOAD


def test_runserver_main_uses_cli_overrides(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(app_target: str, **kwargs: object) -> None:
        captured["app_target"] = app_target
        captured["kwargs"] = kwargs

    monkeypatch.setattr("uniquode.runserver.uvicorn.run", fake_run)

    runserver_main(["--host", "0.0.0.0", "--port", "9000", "--no-reload"])

    assert captured["app_target"] == APP_TARGET
    assert captured["kwargs"] == {
        "host": "0.0.0.0",
        "port": 9000,
        "reload": False,
    }
