from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, FastAPI

from uniquode.routes.health import router as health_router
from uniquode.views import HomePageView
from wevra.web.routes import (
    HtmlRouteDefinition,
    ModuleRoutes,
    register_configured_module_routes,
)


@dataclass(frozen=True, slots=True)
class PublicRouteSet:
    """Stable route names are the URL-generation contract for the public UI."""

    page_routes: tuple[HtmlRouteDefinition, ...]
    api_routers: tuple[APIRouter, ...] = ()


def build_public_route_set() -> PublicRouteSet:
    return PublicRouteSet(
        page_routes=(
            HtmlRouteDefinition(
                path="/",
                name="public:home",
                methods=("GET",),
                surface="page",
                view=HomePageView(),
            ),
        ),
    )


def build_uniquode_module_routes() -> ModuleRoutes:
    route_set = build_public_route_set()
    return ModuleRoutes(
        page_routes=route_set.page_routes,
        api_routers=(health_router, *route_set.api_routers),
    )


module_routes = build_uniquode_module_routes()


def register_routes(app: FastAPI) -> None:
    register_configured_module_routes(
        app,
        app.state.settings,
        app.state.html_dispatcher,
    )
