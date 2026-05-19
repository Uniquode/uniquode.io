import inspect

from fastapi import FastAPI
from fastapi.routing import APIRoute

from uniquode.app import create_app
from uniquode.asgi import app
from uniquode.routes.health import health


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
