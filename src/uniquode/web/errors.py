from dataclasses import dataclass
from http import HTTPStatus
from typing import Literal, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from uniquode.web.renderer import TemplateRenderer
from uniquode.web.theme import theme_template_context

RouteSurface = Literal["page", "partial", "api", "static"]

API_PATH_PREFIX = "/api/"
PARTIAL_PATH_PREFIX = "/partials/"


@dataclass(frozen=True, slots=True)
class EmptyBodyResponseException(Exception):
    status_code: int


@dataclass(frozen=True, slots=True)
class ErrorPresentation:
    status_code: int
    heading: str
    detail: str


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(EmptyBodyResponseException, _handle_empty_body_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_exception)


def _handle_empty_body_error(request: Request, exc: Exception) -> Response:
    empty_body_exc = cast("EmptyBodyResponseException", exc)
    return Response(status_code=empty_body_exc.status_code)


def _handle_http_exception(request: Request, exc: Exception) -> Response:
    http_exc = cast("StarletteHTTPException", exc)
    presentation = _build_error_presentation(
        http_exc.status_code,
        detail=_normalise_http_detail(http_exc.status_code, http_exc.detail),
    )
    return _build_error_response(request, presentation)


def _handle_validation_error(request: Request, exc: Exception) -> Response:
    validation_exc = cast("RequestValidationError", exc)
    presentation = _build_error_presentation(422, detail="The request was invalid.")
    if _resolve_route_surface(request) == "api":
        return JSONResponse(
            status_code=422,
            content={
                "error": presentation.heading,
                "detail": presentation.detail,
                "status_code": presentation.status_code,
                "errors": validation_exc.errors(),
            },
        )

    return _build_error_response(request, presentation)


def _handle_unexpected_exception(request: Request, exc: Exception) -> Response:
    presentation = _build_error_presentation(500)
    return _build_error_response(request, presentation)


def _build_error_response(
    request: Request, presentation: ErrorPresentation
) -> Response:
    surface = _resolve_route_surface(request)
    if surface == "api":
        return JSONResponse(
            status_code=presentation.status_code,
            content={
                "error": presentation.heading,
                "detail": presentation.detail,
                "status_code": presentation.status_code,
            },
        )
    if surface == "static":
        return PlainTextResponse(
            presentation.heading,
            status_code=presentation.status_code,
        )

    renderer = request.app.state.renderer
    if not isinstance(renderer, TemplateRenderer):  # pragma: no cover - defensive
        raise RuntimeError("Template renderer is not configured on the application.")

    context = theme_template_context(request) | {
        "page_title": f"{presentation.status_code} {presentation.heading}",
        "heading": presentation.heading,
        "detail": presentation.detail,
        "status_code": str(presentation.status_code),
    }

    if surface == "partial":
        return renderer.render_partial(
            "errors/fragment.html",
            request,
            context,
            status_code=presentation.status_code,
        )

    return renderer.render_page(
        "errors/base.html",
        request,
        context,
        status_code=presentation.status_code,
    )


def _resolve_route_surface(request: Request) -> RouteSurface:
    path = request.url.path
    static_mount_path = request.app.state.settings.static_mount_path
    if path == static_mount_path or path.startswith(f"{static_mount_path}/"):
        return "static"
    if path.startswith(API_PATH_PREFIX):
        return "api"
    if path.startswith(PARTIAL_PATH_PREFIX):
        return "partial"
    return "page"


def _build_error_presentation(
    status_code: int, *, detail: str | None = None
) -> ErrorPresentation:
    heading = _reason_phrase(status_code)
    fallback_detail = _default_detail(status_code, heading)
    return ErrorPresentation(
        status_code=status_code,
        heading=heading,
        detail=detail if isinstance(detail, str) and detail else fallback_detail,
    )


def _normalise_http_detail(status_code: int, detail: str | None) -> str | None:
    if not isinstance(detail, str) or not detail:
        return None
    if detail == _reason_phrase(status_code):
        return None

    return detail


def _reason_phrase(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Request Failed"


def _default_detail(status_code: int, heading: str) -> str:
    return _DEFAULT_DETAILS.get(
        status_code, f"The request could not be completed ({status_code} {heading})."
    )


_DEFAULT_DETAILS: dict[int, str] = {
    400: "The request could not be understood.",
    401: "Authentication is required to access this resource.",
    403: "You do not have permission to access this resource.",
    404: "The requested resource could not be found.",
    405: "The request method is not allowed for this resource.",
    409: "The request could not be completed because of a conflict.",
    422: "The request was invalid.",
    429: "Too many requests were made in a short period.",
    500: "An internal server error prevented the request from completing.",
}
