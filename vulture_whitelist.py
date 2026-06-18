# ruff: noqa: B018
# Vulture whitelist: application entry points discovered by frameworks.

_KNOWN_WHITELIST_NAMES = frozenset(
    {
        "csrf",
        "csrf_token_secret_configured",
        "health",
        "home",
        "module_routers",
        "renderer",
        "route_prefixes",
        "security_header_options",
        "static_app",
        "static_mount_path",
        "template_root",
    }
)


class _Whitelist:
    def __getattr__(self, name: str) -> object:
        if name not in _KNOWN_WHITELIST_NAMES:
            raise AttributeError(name)
        return None


_ = _Whitelist()

_.health  # FastAPI route handler registered through APIRouter.
_.home  # FastAPI route handler registered through APIRouter.
_.renderer  # Stored on app.state for rendering helpers and error handlers.
_.static_mount_path  # Stored on app.state for Wybra web static handling.
_.csrf  # Stored on app.state for Wybra web rendering and CSRF validation.
_.security_header_options  # Stored on app.state for Wybra web setup.
_.static_app  # Stored on app.state for Wybra web static mounting.
_.template_root  # Stored on app.state for Wybra web template loading.
_.module_routers  # Module route surface discovered by Wybra composition.
_.route_prefixes  # Settings protocol property read by Wybra route composition.
_.csrf_token_secret_configured  # Settings field inspected by validation/tests.
