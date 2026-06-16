from fastapi import APIRouter

from uniquode_io.views import home

router = APIRouter()
router.get("/", include_in_schema=False, name="public:home")(home)


@router.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


module_routers = {
    "default": router,
}
