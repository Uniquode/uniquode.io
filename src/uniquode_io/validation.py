from pathlib import Path

from fastapi.routing import APIRoute
from wybra.tools.validation.core import ValidationCheck, ValidationResult, record_check

HOME_TEMPLATE = "public/pages/home.html"
HOME_STATIC_ASSETS = ("styles/home.css",)
HOME_ROUTE_NAME = "public:home"
HOME_ROUTE_PATH = "/"
HEALTH_ROUTE_PATH = "/health"


def validate_app(_settings: object) -> ValidationResult:
    errors: list[str] = []
    checks: list[ValidationCheck] = []
    app_root = Path(__file__).resolve().parent
    routes = _app_routes()

    record_check(
        checks,
        errors,
        passed=any(
            route.path == HOME_ROUTE_PATH and route.name == HOME_ROUTE_NAME
            for route in routes
        ),
        description=f"home route exists: {HOME_ROUTE_PATH}",
        error=f"Missing home route: {HOME_ROUTE_PATH}",
    )
    record_check(
        checks,
        errors,
        passed=any(route.path == HEALTH_ROUTE_PATH for route in routes),
        description=f"health route exists: {HEALTH_ROUTE_PATH}",
        error=f"Missing health route: {HEALTH_ROUTE_PATH}",
    )

    template_path = app_root / "templates" / HOME_TEMPLATE
    record_check(
        checks,
        errors,
        passed=template_path.is_file(),
        description=f"home page template exists: {HOME_TEMPLATE}",
        error=f"Missing home page template: {template_path}",
    )

    for asset in HOME_STATIC_ASSETS:
        asset_path = app_root / "static" / asset
        record_check(
            checks,
            errors,
            passed=asset_path.is_file(),
            description=f"home page static asset exists: {asset}",
            error=f"Missing home page static asset: {asset_path}",
        )

    return ValidationResult(
        name="uniquode_io",
        errors=tuple(errors),
        checks=tuple(checks),
    )


def _app_routes() -> tuple[APIRoute, ...]:
    from uniquode_io.routes import router

    return tuple(route for route in router.routes if isinstance(route, APIRoute))


validation_targets = {"uniquode_io": validate_app}

__all__ = ("validate_app", "validation_targets")
