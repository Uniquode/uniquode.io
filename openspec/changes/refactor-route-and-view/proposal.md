## Why

The current route/view model is too coupled: module routes can be prefixed by
application configuration, but feature modules still hard-code most route paths
as absolute paths and often split one logical endpoint into separate page and
submit route declarations. This makes module mounting, reverse URL naming, view
method handling, and error handling harder to reason about than they should be
while the `wevra.web` API is still being shaped.

## What Changes

- **BREAKING**: Replace the current `ModuleRoutes(page_routes=..., partial_routes=..., api_routers=...)`
  declaration style with a declarative route map owned by `wevra.web`.
- Introduce `ModuleRoutes(namespace=..., routes={...})`, where route keys define
  default logical names and relative paths.
- Let application configuration choose a module mount point once, such as
  `[routes] "wevra.auth" = "/account"`, and have module-relative routes mount
  beneath that prefix.
- Preserve absolute route paths as explicit bypasses for special cases.
- Add a Django-style class-based `View` dispatch model where a view declares the
  HTTP methods it supports and implements `get`, `post`, `put`, `delete`,
  `patch`, or other method handlers as needed.
- Support `Route(function)` for plain function handlers where the request is the
  first required argument and the function may decide method handling from the
  request.
- Add reusable method helpers such as `can_handle(request, methods)` and
  `invalid_method(request, methods)` for both class views and function views.
- Instantiate view classes or factories lazily rather than at module import or
  route declaration time.
- Add top-level dispatcher exception handling so exceptions raised by route
  handlers are converted into valid page, partial, or API responses through a
  global `wevra.web` exception-handling boundary.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `html-ui-foundation`: Refactor route declaration, view dispatch, method
  handling, module mount semantics, reverse route naming, and dispatcher-level
  exception handling in `wevra.web`.

## Impact

- Affected code includes `wevra.web.routes`, `wevra.web.views`,
  `wevra.web.errors`, `wevra.web.validation`, `wevra.auth.routes`,
  `uniquode.routes`, route templates that call `request.url_for(...)`, and
  tests around route composition, web validation, error rendering, and auth
  pages.
- Existing internal route names such as `identity:login-submit` may be replaced
  by method-dispatching logical route names such as `auth:login`.
- No new runtime dependency is expected.
