from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal, Protocol

from fastapi import FastAPI, Request
from fastapi.responses import Response

from uniquode.web.renderer import TemplateRenderer

HtmlSurface = Literal["page", "partial"]


class HtmlView(Protocol):
    async def render(
        self, request: Request, renderer: TemplateRenderer
    ) -> Response: ...


@dataclass(frozen=True, slots=True)
class HtmlRouteDefinition:
    path: str
    name: str
    methods: tuple[str, ...]
    surface: HtmlSurface
    view: HtmlView


@dataclass(slots=True)
class HtmlDispatcher:
    renderer: TemplateRenderer
    _routes: list[HtmlRouteDefinition] = field(default_factory=list)

    def register(self, definitions: Iterable[HtmlRouteDefinition]) -> None:
        self._routes.extend(definitions)

    def select_view(self, route_name: str, method: str) -> HtmlView:
        for definition in self._routes:
            if definition.name == route_name and method in definition.methods:
                return definition.view

        raise LookupError(f"Unknown HTML route: {route_name} [{method}]")

    async def dispatch(self, route_name: str, request: Request) -> Response:
        return await self.select_view(route_name, request.method).render(
            request, self.renderer
        )


def _build_endpoint(dispatcher: HtmlDispatcher, route_name: str):
    async def endpoint(request: Request) -> Response:
        return await dispatcher.dispatch(route_name, request)

    return endpoint


def register_html_routes(
    app: FastAPI,
    dispatcher: HtmlDispatcher,
    definitions: Iterable[HtmlRouteDefinition],
) -> None:
    route_definitions = tuple(definitions)
    dispatcher.register(route_definitions)
    for definition in route_definitions:
        is_partial_path = definition.path.startswith("/partials/")
        if definition.surface == "partial" and not is_partial_path:
            raise ValueError(
                f"Partial HTML routes must live under /partials/: {definition.path}"
            )
        if definition.surface == "page" and is_partial_path:
            raise ValueError(
                f"Page HTML routes cannot live under /partials/: {definition.path}"
            )
        app.add_api_route(
            definition.path,
            _build_endpoint(dispatcher, definition.name),
            methods=list(definition.methods),
            include_in_schema=False,
            name=definition.name,
        )
