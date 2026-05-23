from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from inspect import isawaitable
from typing import Any, cast
from urllib.parse import parse_qs

from fastapi import Request
from fastapi.responses import Response

from uniquode.web.dispatcher import HtmlView
from uniquode.web.renderer import TemplateRenderer
from uniquode.web.theme import (
    normalise_theme_mode,
    set_theme_mode_cookie,
    set_theme_mode_trigger,
    theme_template_context,
)

ContextBuilder = Callable[[Request], dict[str, Any] | Awaitable[dict[str, Any]]]


async def _resolve_context(
    builder: ContextBuilder | None, request: Request
) -> dict[str, Any]:
    if builder is None:
        return {}

    context = builder(request)
    if isawaitable(context):
        return cast("dict[str, Any]", await context)

    return context


@dataclass(frozen=True, slots=True)
class TemplateView(HtmlView):
    template_name: str
    context_builder: ContextBuilder | None = None

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        context = theme_template_context(request) | await _resolve_context(
            self.context_builder, request
        )
        return renderer.render_page(self.template_name, request, context)


def _build_home_context(request: Request) -> dict[str, Any]:
    return {
        "page_title": "uniquode",
        "theme_update_path": request.url_for("public:partial:theme-mode"),
    }


def _build_theme_selector_context(request: Request) -> dict[str, Any]:
    return {
        "theme_update_path": request.url_for("public:partial:theme-mode"),
    }


@dataclass(frozen=True, slots=True)
class HomePageView(TemplateView):
    template_name: str = "public/pages/home.html"
    context_builder: ContextBuilder | None = _build_home_context


@dataclass(frozen=True, slots=True)
class ThemeStatusPartialView(TemplateView):
    template_name: str = "components/theme_selector.html"
    context_builder: ContextBuilder | None = _build_theme_selector_context


@dataclass(frozen=True, slots=True)
class ThemeModePartialView(HtmlView):
    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        body = (await request.body()).decode("utf-8")
        form_data = parse_qs(body, keep_blank_values=True)
        submitted_mode = next(iter(form_data.get("theme_mode", ["auto"])), "auto")
        theme_mode = normalise_theme_mode(submitted_mode)
        context = theme_template_context(
            request, theme_mode=theme_mode
        ) | _build_theme_selector_context(request)
        response = renderer.render_partial(
            "components/theme_selector.html", request, context
        )
        set_theme_mode_cookie(response, theme_mode)
        set_theme_mode_trigger(response, theme_mode)
        return response
