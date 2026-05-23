from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from uniquode.routes import register_routes
from uniquode.settings import Settings
from uniquode.web.dispatcher import HtmlDispatcher
from uniquode.web.renderer import TemplateRenderer


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings()
    app = FastAPI(title=app_settings.app_name)
    app.state.settings = app_settings
    app.state.renderer = TemplateRenderer(app_settings.template_root)
    app.state.html_dispatcher = HtmlDispatcher(app.state.renderer)
    app.mount(
        app_settings.static_mount_path,
        StaticFiles(directory=app_settings.static_root, check_dir=False),
        name="static",
    )
    register_routes(app)
    return app
