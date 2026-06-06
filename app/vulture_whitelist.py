# ruff: noqa: B018
# Vulture whitelist: application entry points discovered by frameworks.


class _Whitelist:
    pass


_ = _Whitelist()

_.health  # FastAPI route handler registered through APIRouter.
_.identity_delivery  # Stored on app.state for identity delivery integrations.
_.fastapi_users  # Stored on app.state for route handlers and tests.
_.module_routes  # Module route surface discovered by Wevra composition.
_.csrf_token_secret_configured  # Settings field inspected by validation/tests.
_.template_name  # TemplateView class attribute consumed by the base view.
_.context_builder  # TemplateView class attribute consumed by the base view.
