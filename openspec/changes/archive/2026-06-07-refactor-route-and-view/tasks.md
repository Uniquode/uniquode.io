## 1. Router Composition Model

- [x] 1.1 Replace the proposed custom `Route(...)` route-map model with a
  FastAPI-native module router surface.
- [x] 1.2 Define `module_routers` as the configured module route export:
  a mapping from stable string labels to `APIRouter` instances.
- [x] 1.3 Update app composition parsing so `[routes."<module>"]` maps router
  labels to include prefixes.
- [x] 1.4 Validate include prefixes using FastAPI-compatible rules: `""` for
  root, otherwise leading `/` and no trailing `/`.
- [x] 1.5 Include configured routers with `app.include_router(router,
  prefix=prefix)`.
- [x] 1.6 Reject missing router-label prefix configuration unless an explicit
  default-prefix mechanism is introduced.
- [x] 1.7 Preserve route name and method/path conflict detection after prefixes
  are applied.

## 2. FastAPI Handler Declaration

- [x] 2.1 Convert route handlers to FastAPI decorators such as `@router.get`,
  `@router.post`, and `@router.api_route(..., methods=[...])`.
- [x] 2.2 Preserve FastAPI path, query, body, form, dependency, and `Request`
  parameter handling.
- [x] 2.3 Define and test the route-module import convention for handlers
  declared outside `routes.py`.
- [x] 2.4 Avoid custom Django-style `View` dispatch unless a handler
  deliberately branches on `request.method` under `@router.api_route`.
- [x] 2.5 Add tests for multi-method handlers, method-specific handlers,
  path parameters, query parameters, forms, and unsupported methods.

## 3. HTML Helpers, CSRF, And Error Handling

- [x] 3.1 Replace dispatcher CSRF enforcement with FastAPI-compatible
  dependencies, router configuration, or helper functions.
- [x] 3.2 Keep reusable rendering/context helpers callable from ordinary
  FastAPI handlers.
- [x] 3.3 Replace dispatcher-level exception handling with FastAPI/Starlette
  exception handlers plus Wevra response helpers.
- [x] 3.4 Define how page, partial, and API route surface metadata is
  represented using FastAPI-compatible mechanisms.
- [x] 3.5 Add tests for handled HTTP exceptions, unhandled exceptions, partial
  errors, API errors, CSRF failures, and host/framework handler registration.
- [x] 3.6 Add configurable `Cross-Origin-Opener-Policy` support with an
  application default and route/router-specific override support for popup
  flows.
- [x] 3.7 Add tests for default COOP headers, disabled defaults,
  popup-oriented overrides such as `same-origin-allow-popups`, and preserving
  explicitly set response headers.

## 4. Module Conversions

- [x] 4.1 Convert `wevra.web` built-in theme routes to module-owned
  `APIRouter` objects.
- [x] 4.2 Convert `wevra.auth` routes to labelled routers, including an
  account router that can mount at `/account` and any global/callback router
  that mounts at root or another configured prefix.
- [x] 4.3 Mount `wevra.auth` account routes under `/account` in application
  composition and verify FastAPI moves the router paths under that prefix.
- [x] 4.4 Convert application public and health routes where the new router
  surface is a better fit.
- [x] 4.5 Update templates to use the revised FastAPI route names and remove
  submit-specific names where GET and POST intentionally share one route.

## 5. Validation And Documentation

- [x] 5.1 Update web validation to inspect `module_routers`, configured router
  labels, include prefixes, route names, methods, paths, and surface metadata.
- [x] 5.2 Update README/OpenSpec references that describe module routes,
  route-prefix configuration, reverse URL names, CSRF, and error handling.
- [x] 5.3 Add stale-API tests or boundary tests so old split route-bucket usage
  does not reappear after conversion.

## 6. Final Validation

- [x] 6.1 Run focused route composition, auth route, app, validation, CSRF, and
  error-handling tests.
- [x] 6.2 Run the full application test suite.
- [x] 6.3 Run Ruff format and lint checks.
- [x] 6.4 Run `ty check src/`.
- [x] 6.5 Run strict OpenSpec validation for `refactor-route-and-view`.
- [x] 6.6 Run strict main spec validation.
- [x] 6.7 Run `git diff --check`.
