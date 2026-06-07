## Context

Before this change, `wevra.web` wrapped FastAPI routing in a custom route
declaration model with separate page, partial, and API route buckets, and HTML
requests flowed through a framework dispatcher.

That layering is doing too much. FastAPI already provides:

- `APIRouter` for module-owned route groups;
- `@router.get`, `@router.post`, and `@router.api_route(..., methods=[...])`
  decorators;
- include-time router prefixes through `app.include_router(router,
  prefix="/...")`;
- function signature parsing for request, path, query, body, form, and
  dependency values;
- method handling and `405` responses;
- exception-handler registration.

The Wevra-specific value is composition across configured modules, not route
dispatch itself. The revised design uses FastAPI routing directly and keeps
Wevra focused on module discovery, router-prefix configuration, validation,
HTML helper conventions, CSRF integration, and error rendering.

## Goals

- Make configured module route composition a thin layer over FastAPI routers.
- Let applications configure where module routers mount.
- Support multiple routers per configured module without baking URL prefixes
  into the reusable module.
- Keep route handlers as ordinary FastAPI-decorated functions.
- Preserve FastAPI path, query, body, form, dependency, and response semantics.
- Avoid a custom Wevra route DSL and avoid Django-style dispatch unless a
  handler deliberately chooses to branch on `request.method`.
- Keep reverse URL names as normal FastAPI/Starlette route names.
- Preserve shared Wevra HTML rendering, CSRF, static/template, validation, and
  exception-handling conventions.
- Provide framework-owned security-header support for
  `Cross-Origin-Opener-Policy` so popup-oriented integrations can be handled
  deliberately.

## Non-Goals

- Do not add a new runtime dependency.
- Do not introduce automatic installed-package route discovery.
- Do not build a replacement for FastAPI routing, dependency injection,
  parameter parsing, or OpenAPI metadata.
- Do not support absolute route paths that bypass an included router prefix.
  Prefix bypass is represented by a separate router mounted with an empty
  prefix.
- Do not require all handlers to receive `Request`; handlers ask FastAPI for
  `Request` only when they need it.

## Module Route Surface

Each configured module may expose routers from `<module>.routes`:

```python
from fastapi import APIRouter

account_router = APIRouter()
callback_router = APIRouter()

module_routers = {
    "account": account_router,
    "callbacks": callback_router,
}
```

Router labels are stable module-local identifiers. They are not URL prefixes.
The host application decides the prefix for each label.

A module with one router should still use an explicit label:

```python
router = APIRouter()

module_routers = {
    "default": router,
}
```

`wevra.web` discovers only the route surface. It does not import host
application modules directly, and it does not know auth/application URL policy.

## Route Prefix Configuration

Application composition config maps module names to router labels and FastAPI
include prefixes:

```toml
[routes."app"]
default = ""

[routes."wevra.auth"]
account = "/account"
callbacks = ""
```

This parses conceptually as:

```python
{
    "app": {"default": ""},
    "wevra.auth": {"account": "/account", "callbacks": ""},
}
```

Composition then includes routers:

```python
for module_name in settings.modules:
    routes_module = import_module(f"{module_name}.routes")
    route_prefixes = configured_route_prefixes_for(module_name)

    for label, router in routes_module.module_routers.items():
        prefix = route_prefixes[label]
        app.include_router(router, prefix=prefix)
```

Prefix validation should match FastAPI include-prefix rules:

- `""` means app root;
- non-empty prefixes must start with `/`;
- non-empty prefixes must not end with `/`.

Missing route configuration for an exposed router label should fail validation
unless a deliberate module/default-prefix mechanism is later introduced. The
safe default is to avoid accidental root exposure when a module adds a new
router.

## Handler Declaration

Handlers use FastAPI decorators on module routers:

```python
@account_router.get("/login", name="auth:login")
async def login_page(request: Request):
    ...


@account_router.post("/login", name="auth:login")
async def login_submit(request: Request):
    ...
```

When one logical endpoint should handle multiple methods, use FastAPI's
multi-method decorator:

```python
@account_router.api_route(
    "/login",
    methods=["GET", "POST"],
    name="auth:login",
)
async def login(request: Request):
    if request.method == "GET":
        ...

    ...
```

Path parameters are declared in the FastAPI path and typed in the handler
signature:

```python
@account_router.get("/users/{user_id}", name="auth:user")
async def user_detail(user_id: int, tab: str | None = None):
    ...
```

`Request` remains optional. Handlers include it only when they need raw request
state, application state, sessions, renderer access, CSRF helpers, or method
branching.

## Handler Import And Decorator Registration

FastAPI decorators register handlers at import time. If decorated handlers live
outside `routes.py`, those handler modules must be imported before Wevra
includes the routers.

Small modules may colocate routers and handlers in `routes.py`.

For larger modules, there are two acceptable patterns:

1. `routes.py` defines routers, then explicitly loads handler modules after the
   routers exist. Handler modules import the routers from their local
   `routes.py` module and decorate functions.
2. A private router-definition module, such as `_routers.py`, defines routers.
   Handler modules import routers from `_routers.py`. `routes.py` imports the
   handler modules for registration and exposes `module_routers`.

The second pattern avoids circular imports most cleanly. The first pattern is
acceptable if `routes.py` defines router objects before importing handler
modules and handler modules import only those router objects rather than
`module_routers`.

`wevra.web` should import only `<module>.routes`; the route module is
responsible for ensuring all decorator registration side effects have occurred.

## Router Inclusion And Conflict Detection

Wevra composition should include FastAPI routers directly. It may still inspect
the resulting route graph before or after inclusion to validate:

- configured module route surfaces are well-formed;
- `module_routers` is a mapping from non-blank string labels to `APIRouter`
  instances;
- each router label has a configured prefix;
- route prefixes obey FastAPI include-prefix rules;
- route names are unique where reverse URL generation requires uniqueness;
- method/path combinations do not accidentally conflict after prefixes are
  applied.

The implementation should prefer FastAPI's own route objects and metadata over
duplicating route declarations.

## HTML Helpers, CSRF, And Forms

Removing the dispatcher also removes the current central CSRF check that runs
before HTML view rendering. The refactor must replace that behaviour with
FastAPI-native integration.

Likely options are:

- route or router dependencies that validate CSRF for unsafe methods;
- a Wevra-provided dependency/helper that modules attach to HTML form routes;
- a router factory that returns an `APIRouter` with standard Wevra HTML
  dependencies.

The first implementation should keep the mechanism explicit and testable. It
must preserve the existing requirement that unsafe form submissions are checked
when CSRF protection is configured.

Rendering helpers can remain reusable functions/classes. They should be called
from ordinary FastAPI handlers rather than requiring a dispatcher-owned
view-render protocol.

## Error Handling

The previous proposal introduced a dispatcher-level exception boundary. With
FastAPI-native routing, exception handling should instead use FastAPI/Starlette
exception handlers and Wevra-provided response helpers.

The error-handling layer should:

- register framework default handlers on the FastAPI application;
- allow host applications or modules to register specialised handlers;
- preserve HTTP status codes for HTTP exceptions;
- return full-page HTML error responses for page routes;
- return fragment-compatible responses for partial routes;
- return machine-oriented responses for API routes;
- leave raw FastAPI route behaviour available where a route opts into it.

Route surface detection may use router-level metadata, route tags,
dependencies, endpoint attributes, or another FastAPI-compatible convention.
The implementation should not require a custom dispatcher.

## Cross-Origin Opener Policy

`Cross-Origin-Opener-Policy` is a response security header, not a CORS or CSRF
setting. It controls opener/window isolation and matters for popup-oriented
flows such as OAuth or payment handling.

Wevra should provide a small security-header mechanism that can:

- set an application default, likely `same-origin`;
- disable the header when explicitly configured as `None`;
- allow specific routes or routers to override the default with values such as
  `same-origin-allow-popups`;
- avoid overwriting a response that already deliberately set the header.

The implementation should use FastAPI/Starlette-compatible middleware,
dependencies, endpoint metadata, or route metadata rather than a dispatcher.

The likely shape is:

- app setup registers middleware that applies the default COOP value;
- a route/router helper or decorator marks endpoint metadata for a specific
  policy override;
- middleware consults the resolved endpoint or route metadata and applies the
  effective value after the handler returns.

For payment or OAuth popup forms, the route that initiates or coordinates the
popup can opt into `same-origin-allow-popups` while the rest of the application
keeps the stricter default.

## Migration Strategy

1. Introduce FastAPI-router discovery and prefix configuration beside the
   current custom route-bucket implementation.
2. Add validation tests for `module_routers`, configured prefixes, missing
   router labels, duplicate route names, and post-prefix method/path conflicts.
3. Add or adapt CSRF and error-handler tests for FastAPI-native routes.
4. Add COOP default and route/handler override tests.
5. Convert `wevra.web` built-in routes to module-owned `APIRouter` objects.
6. Convert `wevra.auth` pages from custom route declarations to decorated
   FastAPI handlers.
7. Convert application public and health routing to the new router surface
   where appropriate.
8. Remove or deprecate the custom route declarations, route buckets, and
   dispatcher once all live modules have moved.

## Open Questions

- Should Wevra provide a router factory for common page/partial/API defaults,
  or should modules use plain `APIRouter` plus explicit dependencies?
- Should duplicate route names be rejected globally, or should validation allow
  FastAPI's existing behaviour when multiple methods share one URL name?
- What is the least intrusive FastAPI-compatible way to mark route surface for
  error-response selection?
- Should COOP overrides share the same endpoint metadata mechanism as route
  surface metadata, or use a separate helper/decorator for clarity?
