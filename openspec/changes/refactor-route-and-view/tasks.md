## 1. Route Model

- [ ] 1.1 Add `Route`, `ModuleRoutes(namespace=..., routes=...)`, route target,
  route surface, and route-name/path derivation primitives under `wevra.web`.
- [ ] 1.2 Define route-key normalisation rules for default path and reverse
  route names, including nested keys such as `password/reset`.
- [ ] 1.3 Support `path=None`, `path=""`, relative paths, and absolute paths
  with clear mount-prefix semantics.
- [ ] 1.4 Preserve route name and method/path conflict detection for composed
  routes.
- [ ] 1.5 Add tests for application route prefixes moving module-relative
  routes while absolute routes bypass the mount.

## 2. View And Handler Dispatch

- [ ] 2.1 Add `HttpMethod`, method normalisation, `can_handle`, and
  `invalid_method` helpers in `wevra.web`.
- [ ] 2.2 Add a class-based `View` dispatch base with Django-style
  `http_method_names` and per-method handler lookup.
- [ ] 2.3 Update `TemplateView` to use the new view dispatch contract.
- [ ] 2.4 Support `Route(function)` for sync and async functions whose first
  required argument is the request.
- [ ] 2.5 Ensure class/factory route targets are constructed lazily rather than
  at module import time.
- [ ] 2.6 Add tests for GET, HEAD, POST, unsupported methods, function views,
  class views, and lazy target construction.

## 3. Dispatcher And Exception Handling

- [ ] 3.1 Refactor `HtmlDispatcher` or its replacement into the top-level
  `wevra.web` request dispatcher for route-map targets.
- [ ] 3.2 Add a dispatcher exception-handler registry that maps exceptions to
  responses by exception type and route surface.
- [ ] 3.3 Preserve page, partial, and API error-response behaviour through the
  dispatcher-level exception boundary.
- [ ] 3.4 Add method-not-allowed handling with correct `Allow` headers.
- [ ] 3.5 Keep app-level FastAPI/Starlette exception handlers as fallback for
  raw FastAPI routes and non-dispatcher failures.
- [ ] 3.6 Add tests for handled HTTP exceptions, unhandled exceptions, partial
  errors, API errors, and host/framework handler registration.

## 4. Module Conversions

- [ ] 4.1 Convert `wevra.web` built-in theme routes to the new route-map
  declaration style.
- [ ] 4.2 Convert `wevra.auth` routes to `ModuleRoutes(namespace="auth", ...)`
  with method-dispatching views such as `auth:login`, `auth:signup`,
  `auth:logout`, and `auth:account`.
- [ ] 4.3 Mount `wevra.auth` under `/account` in application composition and
  verify relative auth routes move under that prefix.
- [ ] 4.4 Convert `uniquode` public and health routes where the new model is a
  better fit, preserving explicit root/absolute route behaviour.
- [ ] 4.5 Update templates to use the new logical reverse route names and remove
  submit-specific reverse names where GET and POST share one route.

## 5. Validation And Documentation

- [ ] 5.1 Update web validation to inspect route-map declarations, generated
  route names, mounted paths, supported methods, view targets, and exception
  handler configuration.
- [ ] 5.2 Update README/OpenSpec references that describe module routes,
  route-prefix configuration, reverse URL names, and error handling.
- [ ] 5.3 Add stale-API tests or boundary tests so old split route-bucket usage
  does not reappear after conversion.

## 6. Final Validation

- [ ] 6.1 Run focused route/view, auth route, app, validation, and error
  handling tests.
- [ ] 6.2 Run the full Python test suite.
- [ ] 6.3 Run Ruff format and lint checks.
- [ ] 6.4 Run `ty check src/`.
- [ ] 6.5 Run strict OpenSpec validation for `refactor-route-and-view`.
- [ ] 6.6 Run strict main spec validation.
- [ ] 6.7 Run `git diff --check`.
