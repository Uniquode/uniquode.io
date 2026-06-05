from __future__ import annotations

from fastapi import FastAPI

from uniquode.routes.health import router as health_router
from web_core.routing import ModuleRoutes, register_configured_module_routes

module_routes = ModuleRoutes(api_routers=(health_router,))


def register_routes(app: FastAPI) -> None:
    register_configured_module_routes(
        app,
        app.state.settings,
        app.state.html_dispatcher,
    )
