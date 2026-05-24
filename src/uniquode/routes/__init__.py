from fastapi import FastAPI

from public.routes import build_public_route_set
from uniquode.identity.routes import build_identity_route_set
from uniquode.routes.health import router as health_router
from uniquode.web.dispatcher import register_html_routes


def register_routes(app: FastAPI) -> None:
    public_route_set = build_public_route_set()
    identity_route_set = build_identity_route_set()
    app.include_router(health_router)
    register_html_routes(app, app.state.html_dispatcher, public_route_set.page_routes)
    register_html_routes(app, app.state.html_dispatcher, identity_route_set.page_routes)
    register_html_routes(
        app, app.state.html_dispatcher, public_route_set.partial_routes
    )
    app.include_router(public_route_set.api_router)
    app.include_router(identity_route_set.api_router)
