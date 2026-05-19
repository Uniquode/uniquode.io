from fastapi import FastAPI

from uniquode.routes.health import router as health_router


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router)
