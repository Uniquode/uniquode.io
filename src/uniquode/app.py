from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from uniquode.identity.delivery import NullIdentityDelivery
from uniquode.identity.users import create_fastapi_users
from uniquode.persistence import close_database, create_database
from uniquode.routes import register_routes
from uniquode.settings import Settings, load_settings
from uniquode.web.csrf import CsrfProtector
from uniquode.web.dispatcher import HtmlDispatcher
from uniquode.web.errors import register_error_handlers
from uniquode.web.renderer import TemplateRenderer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        database = getattr(app.state, "database", None)
        if database is not None:
            await close_database(database)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or load_settings()
    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.state.settings = app_settings
    app.state.database = create_database(app_settings)
    app.state.identity_delivery = NullIdentityDelivery()
    app.state.fastapi_users = create_fastapi_users(app_settings.identity_options)
    csrf_cookie_secure = app_settings.csrf_cookie_secure
    if csrf_cookie_secure is None:  # pragma: no cover - Settings normalises this
        raise RuntimeError("CSRF cookie security setting was not normalised.")
    app.state.csrf = CsrfProtector(
        app_settings.csrf_token_secret,
        cookie_secure=csrf_cookie_secure,
    )
    app.state.renderer = TemplateRenderer(app_settings.template_root, app.state.csrf)
    app.state.html_dispatcher = HtmlDispatcher(app.state.renderer, app.state.csrf)
    register_error_handlers(app)
    app.mount(
        app_settings.static_mount_path,
        StaticFiles(directory=app_settings.static_root, check_dir=False),
        name="static",
    )
    register_routes(app)
    return app
