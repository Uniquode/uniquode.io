## Why

The current route/view model is too coupled and too custom. `wevra.web`
composes module route contributions, but feature modules still hard-code route
paths as absolute paths and declare routes through a Wevra-specific
route-definition layer that partially duplicates FastAPI and Starlette routing.

After separating Wevra into its own project, the cleaner boundary is to let
FastAPI remain the route declaration and dispatch mechanism. Wevra should own
module discovery, router inclusion, validation, rendering helpers, CSRF
integration, and exception handling conventions rather than inventing a
parallel routing framework.

## What Changes

- **BREAKING**: Replace the current Wevra-specific HTML route-definition API
  with module-owned FastAPI `APIRouter` objects.
- Modules expose route surfaces from `<module>.routes` through a
  `module_routers` mapping of stable router labels to `APIRouter` instances.
- Application configuration maps configured module router labels to FastAPI
  include prefixes, for example:

  ```toml
  [routes."wevra.auth"]
  account = "/account"
  callbacks = ""
  ```

- Wevra composition imports each configured module's route surface and includes
  each declared router with the configured prefix by calling
  `app.include_router(router, prefix=prefix)`.
- Route handlers use FastAPI decorators directly, such as `@router.get(...)`,
  `@router.post(...)`, and `@router.api_route(..., methods=[...])`.
- Route paths inside routers remain normal FastAPI paths beginning with `/`;
  global routes use a router mounted with an empty prefix rather than an
  absolute-path bypass rule.
- Reverse URL names are normal FastAPI/Starlette route names supplied by the
  route decorators.
- View/helper code may live outside `routes.py`, but route modules are
  responsible for importing handler modules so decorator registration has
  happened before Wevra includes the routers.
- Replace dispatcher-owned method handling with FastAPI route method handling
  and handler-level branching where `@router.api_route(..., methods=[...])` is
  used.
- Replace dispatcher-level exception handling with FastAPI/Starlette exception
  handlers plus Wevra-provided rendering and response helpers for page,
  partial, and API surfaces.
- Add reusable `Cross-Origin-Opener-Policy` handling so applications can set a
  secure default and opt specific popup-oriented routes into values such as
  `same-origin-allow-popups`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-foundation`: Refactor module route declaration and composition to
  use FastAPI `APIRouter` objects, configured router prefixes, FastAPI route
  decorators, FastAPI method dispatch, and FastAPI/Starlette exception handling
  conventions.

## Impact

- Affected code includes `wevra.web.routes`, `wevra.web.validation`,
  `wevra.web.errors`, `wevra.web.forms`, `wevra.auth.routes`, application
  routes, templates that call `request.url_for(...)`, and tests around route
  composition, configured prefixes, validation, CSRF, error rendering, and auth
  pages, and security-header behaviour.
- Existing submit-specific route names may be replaced or consolidated where a
  single FastAPI route handles multiple methods with
  `@router.api_route(...)`.
- No new runtime dependency is expected.
