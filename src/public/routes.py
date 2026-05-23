from dataclasses import dataclass

from fastapi import APIRouter, Request

from public.views import (
    HomePageView,
    ThemeModePartialView,
    ThemeStatusPartialView,
)
from uniquode.web.dispatcher import HtmlRouteDefinition
from uniquode.web.theme import resolve_theme_mode


@dataclass(frozen=True, slots=True)
class PublicRouteSet:
    """Stable route names are the reverse-resolution contract for the public UI."""

    page_routes: tuple[HtmlRouteDefinition, ...]
    partial_routes: tuple[HtmlRouteDefinition, ...]
    api_router: APIRouter


async def theme_state(request: Request) -> dict[str, str]:
    return {"theme_mode": resolve_theme_mode(request)}


def build_public_route_set() -> PublicRouteSet:
    api_router = APIRouter(prefix="/api/public")
    api_router.add_api_route(
        "/theme",
        theme_state,
        methods=["GET"],
        include_in_schema=False,
        name="public:api:theme",
    )

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
        partial_routes=(
            HtmlRouteDefinition(
                path="/partials/theme-selector",
                name="public:partial:theme-selector",
                methods=("GET",),
                surface="partial",
                view=ThemeStatusPartialView(),
            ),
            HtmlRouteDefinition(
                path="/partials/theme-mode",
                name="public:partial:theme-mode",
                methods=("POST",),
                surface="partial",
                view=ThemeModePartialView(),
            ),
        ),
        api_router=api_router,
    )
