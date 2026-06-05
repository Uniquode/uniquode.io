from dataclasses import dataclass

from fastapi import APIRouter

from public.views import HomePageView
from web_core.routing import HtmlRouteDefinition, ModuleRoutes


@dataclass(frozen=True, slots=True)
class PublicRouteSet:
    """Stable route names are the reverse-resolution contract for the public UI."""

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


def build_public_module_routes() -> ModuleRoutes:
    route_set = build_public_route_set()
    return ModuleRoutes(
        page_routes=route_set.page_routes,
        api_routers=route_set.api_routers,
    )


module_routes = build_public_module_routes()
