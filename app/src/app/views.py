from dataclasses import dataclass
from typing import Any

from fastapi import Request
from wevra.web.views.templates import ContextBuilder, TemplateView


def _build_home_context(_request: Request) -> dict[str, Any]:
    return {
        "page_title": "uniquode",
    }


@dataclass(frozen=True, slots=True)
class HomePageView(TemplateView):
    template_name: str = "public/pages/home.html"
    context_builder: ContextBuilder | None = _build_home_context
