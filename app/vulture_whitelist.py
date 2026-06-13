# ruff: noqa: B018
# Vulture whitelist: application entry points discovered by frameworks.


class _Whitelist:
    pass


_ = _Whitelist()

_.health  # FastAPI route handler registered through APIRouter.
_.home  # FastAPI route handler registered through APIRouter.
_.renderer  # Stored on app.state for rendering helpers and error handlers.
_.static_mount_path  # Stored on app.state for Wevra web static handling.
_.csrf  # Stored on app.state for Wevra web rendering and CSRF validation.
_.security_header_options  # Stored on app.state for Wevra web setup.
_.static_app  # Stored on app.state for Wevra web static mounting.
_.template_root  # Stored on app.state for Wevra web template loading.
_.module_routers  # Module route surface discovered by Wevra composition.
_.route_prefixes  # Settings protocol property read by Wevra route composition.
_.csrf_token_secret_configured  # Settings field inspected by validation/tests.
