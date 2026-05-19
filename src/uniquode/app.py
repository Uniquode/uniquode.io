from fastapi import FastAPI

from uniquode.routes import register_routes
from uniquode.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings()
    app = FastAPI(title=app_settings.app_name)
    app.state.settings = app_settings
    register_routes(app)
    return app
