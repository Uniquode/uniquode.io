"""Shared module composition defaults for application tests."""

TEST_ROUTE_PREFIXES = {
    "uniquode_io": {"default": ""},
    "wybra.widgets": {"partials": "", "api": ""},
    "wybra.messages": {},
    "wybra.assets": {},
    "wybra.security": {},
    "wybra.forms": {},
    "wybra.api": {},
    "wybra.template": {},
    "wybra.errors": {},
    "wybra.db": {},
    "wybra.auth": {"account": "/account", "api": ""},
}
WEB_RUNTIME_MODULES = (
    "wybra.messages",
    "wybra.assets",
    "wybra.security",
    "wybra.forms",
    "wybra.api",
    "wybra.template",
    "wybra.errors",
)
PUBLIC_WEB_MODULES = ("uniquode_io", *WEB_RUNTIME_MODULES)
AUTH_WEB_MODULES = (*WEB_RUNTIME_MODULES, "wybra.db", "wybra.auth")
FULL_APP_MODULES = (
    "uniquode_io",
    "wybra.widgets",
    *AUTH_WEB_MODULES,
)
