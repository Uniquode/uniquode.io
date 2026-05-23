import json
from typing import Literal, cast

from fastapi import Request
from fastapi.responses import Response

ThemeMode = Literal["auto", "light", "dark"]
THEME_MODES: tuple[ThemeMode, ...] = ("auto", "light", "dark")
THEME_MODE_COOKIE = "theme_mode"
THEME_MODE_ICONS: dict[ThemeMode, str] = {
    "auto": "computer",
    "light": "light_mode",
    "dark": "dark_mode",
}


def normalise_theme_mode(value: str | None) -> ThemeMode:
    if value in THEME_MODES:
        return cast(ThemeMode, value)

    return "auto"


def resolve_theme_mode(request: Request) -> ThemeMode:
    return normalise_theme_mode(request.cookies.get(THEME_MODE_COOKIE))


def next_theme_mode(theme_mode: ThemeMode) -> ThemeMode:
    current_index = THEME_MODES.index(theme_mode)
    return THEME_MODES[(current_index + 1) % len(THEME_MODES)]


def set_theme_mode_cookie(response: Response, theme_mode: ThemeMode) -> None:
    response.set_cookie(
        THEME_MODE_COOKIE,
        theme_mode,
        httponly=True,
        max_age=31_536_000,
        path="/",
        samesite="lax",
    )


def set_theme_mode_trigger(response: Response, theme_mode: ThemeMode) -> None:
    response.headers["HX-Trigger"] = json.dumps(
        {"theme-mode-changed": {"theme_mode": theme_mode}}
    )


def theme_template_context(
    request: Request, *, theme_mode: ThemeMode | None = None
) -> dict[str, str]:
    current_theme = theme_mode or resolve_theme_mode(request)
    return {
        "theme_mode": current_theme,
        "theme_label": current_theme.title(),
        "theme_attribute": "" if current_theme == "auto" else current_theme,
        "theme_next_mode": next_theme_mode(current_theme),
        "theme_icon_name": THEME_MODE_ICONS[current_theme],
    }
