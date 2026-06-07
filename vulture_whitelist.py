# ruff: noqa: B018
# Vulture whitelist: application entry points discovered by frameworks.


class _Whitelist:
    pass


_ = _Whitelist()

_.health  # FastAPI route handler registered through APIRouter.
_.home  # FastAPI route handler registered through APIRouter.
_.renderer  # Stored on app.state for rendering helpers and error handlers.
_.identity_delivery  # Stored on app.state for identity delivery integrations.
_.fastapi_users  # Stored on app.state for route handlers and tests.
_.module_routers  # Module route surface discovered by Wevra composition.
_.route_prefixes  # Settings protocol property read by Wevra route composition.
_.csrf_token_secret_configured  # Settings field inspected by validation/tests.
