from fastapi import APIRouter, FastAPI, Request
from wevra.web.rendering import render_page

from app.routes.health import router as health_router
from app.views import build_home_context

router = APIRouter()


@router.get("/", include_in_schema=False, name="public:home")
async def home(request: Request):
    return render_page(
        request,
        "public/pages/home.html",
        build_home_context(request),
    )


router.include_router(health_router)

module_routers = {
    "default": router,
}


def register_routes(app: FastAPI) -> None:
    app.include_router(router)
