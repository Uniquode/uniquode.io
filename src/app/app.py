from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp
from wevra.core.resources import PackageResourceSource
from wevra.db.persistence import close_database, create_database
from wevra.web.context import (
    resolve_context_providers,
    set_request_context,
    validate_context_providers,
)
from wevra.web.errors import ErrorHandlerOptions, register_error_handlers
from wevra.web.forms.csrf import CsrfProtector
from wevra.web.rendering import (
    RESERVED_TEMPLATE_CONTEXT_KEYS,
    TemplateRenderer,
)
from wevra.web.routes.contracts import API_PATH_PREFIX
from wevra.web.routes.discovery import (
    context_providers_from_modules,
    static_sources_from_modules,
    template_sources_from_modules,
)
from wevra.web.security import SecurityHeaderOptions, register_security_headers
from wevra.web.staticfiles import ComposedStaticFiles, NoStaticFiles

from app.auth_settings import load_app_auth_settings
from app.routes import register_routes
from app.settings import Settings, load_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        database = getattr(app.state, "database", None)
        if database is not None:
            await close_database(database)


async def template_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if _should_resolve_template_context(request):
        providers = request.app.state.template_context_providers
        context = await resolve_context_providers(
            providers,
            request,
            reserved_keys=RESERVED_TEMPLATE_CONTEXT_KEYS,
        )
        set_request_context(request, context)

    return await call_next(request)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or load_settings()
    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.state.settings = app_settings
    app.state.static_mount_path = app_settings.static_mount_path
    app.state.database = create_database(app_settings)
    if _identity_enabled(app_settings):
        _configure_identity(app, app_settings)
    csrf_cookie_secure = app_settings.csrf_cookie_secure
    if csrf_cookie_secure is None:  # pragma: no cover - Settings normalises this
        raise RuntimeError("CSRF cookie security setting was not normalised.")
    app.state.csrf = CsrfProtector(
        app_settings.csrf_token_secret,
        cookie_secure=csrf_cookie_secure,
    )
    template_sources = template_sources_from_modules(app_settings.modules)
    template_root = (
        app_settings.template_root
        if app_settings.uses_filesystem_template_root or not template_sources
        else None
    )
    app.state.renderer = TemplateRenderer(
        template_root=template_root,
        csrf=app.state.csrf,
        template_sources=template_sources,
        auto_reload=app_settings.template_auto_reload,
        cache_size=app_settings.template_cache_size,
    )
    app.state.template_context_providers = validate_context_providers(
        context_providers_from_modules(app_settings.modules)
    )
    app.middleware("http")(template_context_middleware)
    register_security_headers(
        app,
        options=SecurityHeaderOptions(
            cross_origin_opener_policy=app_settings.cross_origin_opener_policy,
        ),
    )
    register_error_handlers(
        app,
        options=ErrorHandlerOptions(static_mount_path=app_settings.static_mount_path),
    )
    static_sources = static_sources_from_modules(app_settings.modules)
    static_app = _static_app(app_settings, static_sources)
    app.mount(
        app_settings.static_mount_path,
        static_app,
        name="static",
    )
    register_routes(app)
    return app


def _identity_enabled(settings: Settings) -> bool:
    return settings.identity_enabled


def _configure_identity(app: FastAPI, settings: Settings) -> None:
    from wevra.auth.delivery import NullIdentityDelivery
    from wevra.auth.sessions import create_fastapi_users

    auth_settings = load_app_auth_settings(settings)
    identity_options = auth_settings.identity_options
    app.state.auth_settings = auth_settings
    app.state.identity_delivery = NullIdentityDelivery()
    app.state.fastapi_users = create_fastapi_users(identity_options)


def _static_app(
    settings: Settings,
    static_sources: tuple[PackageResourceSource, ...],
) -> ASGIApp:
    if settings.uses_filesystem_static_root:
        static_root = settings.static_root
        if static_root is None:  # pragma: no cover - Settings normalises this
            raise RuntimeError("Filesystem static root was not normalised.")
        return StaticFiles(directory=static_root, check_dir=False)
    if static_sources:
        return ComposedStaticFiles(static_sources)

    return NoStaticFiles()


def _should_resolve_template_context(request: Request) -> bool:
    path = request.url.path
    settings = request.app.state.settings
    return not (
        _matches_path_prefix(path, settings.static_mount_path)
        or _matches_path_prefix(path, API_PATH_PREFIX)
    )


def _matches_path_prefix(path: str, prefix: str) -> bool:
    normalised_prefix = "/" + prefix.strip("/")
    return path == normalised_prefix or path.startswith(f"{normalised_prefix}/")
