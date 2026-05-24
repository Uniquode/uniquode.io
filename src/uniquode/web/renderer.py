from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from uniquode.web.csrf import CsrfProtector


@dataclass(slots=True)
class TemplateRenderer:
    template_root: Path
    csrf: CsrfProtector | None = None
    environment: Environment = field(init=False)

    def __post_init__(self) -> None:
        self.environment = Environment(
            loader=FileSystemLoader(str(self.template_root)),
            autoescape=select_autoescape(("html", "xml")),
        )

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        return self.environment.get_template(template_name).render(context)

    @staticmethod
    def _resolve_route_name(request: Request) -> str:
        route = request.scope.get("route")
        route_name = getattr(route, "name", None)
        if isinstance(route_name, str):
            return route_name

        return "unknown"

    def _template_context(
        self,
        request: Request,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        base_context: dict[str, Any] = {
            "request": request,
            "route_name": self._resolve_route_name(request),
        }
        csrf_context = self.csrf.token_context(request) if self.csrf is not None else {}
        internal_keys = base_context.keys() | csrf_context.keys()
        overlapping_keys = internal_keys & context.keys()
        if overlapping_keys:
            keys = ", ".join(sorted(overlapping_keys))
            raise ValueError(f"Template context overrides internal keys: {keys}")

        return context | csrf_context | base_context

    def render_page(
        self,
        template_name: str,
        request: Request,
        context: dict[str, Any],
        *,
        status_code: int = 200,
    ) -> HTMLResponse:
        template_context = self._template_context(request, context)
        response = HTMLResponse(
            self.render_template(
                template_name,
                template_context,
            ),
            status_code=status_code,
        )
        if self.csrf is not None:
            self.csrf.set_cookie(request, response)

        return response

    def render_partial(
        self,
        template_name: str,
        request: Request,
        context: dict[str, Any],
        *,
        status_code: int = 200,
    ) -> HTMLResponse:
        return self.render_page(
            template_name, request, context, status_code=status_code
        )
