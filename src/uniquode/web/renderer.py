from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclass(slots=True)
class TemplateRenderer:
    template_root: Path
    environment: Environment = field(init=False)

    def __post_init__(self) -> None:
        self.environment = Environment(
            loader=FileSystemLoader(str(self.template_root)),
            autoescape=select_autoescape(("html", "xml")),
        )

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        return self.environment.get_template(template_name).render(context)

    def render_page(
        self,
        template_name: str,
        request: Request,
        context: dict[str, Any],
        *,
        status_code: int = 200,
    ) -> HTMLResponse:
        return HTMLResponse(
            self.render_template(
                template_name,
                {"request": request, "route_name": request.scope["route"].name}
                | context,
            ),
            status_code=status_code,
        )

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
