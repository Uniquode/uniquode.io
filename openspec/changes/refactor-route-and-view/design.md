## Context

`wevra.web` currently composes route contributions from configured modules, but
the declaration model still exposes too much low-level routing detail to each
module. Auth pages are the clearest example: mounting `wevra.auth` at
`/account` should move relative auth routes to `/account/...`, but the current
auth routes are declared as absolute paths such as `/login`, `/signup`, and
`/logout`. Changing the mount requires edits in route declarations, app
configuration, and sometimes templates/tests.

The intended model is:

- modules declare logical routes;
- the application chooses module mount points;
- relative routes mount under the application-selected prefix;
- absolute routes intentionally bypass that prefix;
- reverse URL names are generated from module namespace and route key;
- views own HTTP method behaviour;
- the dispatcher owns handler invocation, method failure responses, and
  top-level exception mapping.

## Goals

- Make route declarations concise and declarative for ordinary module routes.
- Keep module route paths portable across application mount points.
- Support both class-based views and plain function handlers.
- Avoid constructing view classes until a route is actually dispatched.
- Make route names predictable and reversible without duplicating route keys.
- Centralise method handling primitives so class and function views behave
  consistently.
- Centralise dispatcher-level exception handling for valid page, partial, and
  API responses.

## Non-Goals

- Do not add a new runtime dependency.
- Do not introduce automatic installed-package route discovery.
- Do not force every route into HTML rendering; a handler may return any valid
  response shape supported by the web dispatch contract.
- Do not remove explicit absolute routes; they remain an escape hatch.
- Do not solve future OpenAPI generation or schema declaration beyond preserving
  enough metadata for current routing and validation.

## Route Declaration Model

Module route surfaces should expose one route table:

```python
module_routes = ModuleRoutes(
    namespace="auth",
    routes={
        "login": Route(LoginView),
        "signup": Route(SignupView),
        "logout": Route(LogoutView),
        "account": Route(AccountView, path=""),
        "password/reset": Route(PasswordResetView),
    },
)
```

The route key is the default source for both:

- the relative path, for example `login` -> `login`;
- the reverse-route name segment, for example `login` -> `auth:login`.

For nested route keys, the default path keeps the slash while the default route
name uses a deterministic, URL-safe name segment. For example,
`password/reset` can resolve to path `password/reset` and route name
`auth:password-reset`.

`Route(path=...)` is an escape hatch:

- `path=None` means derive the relative path from the route key;
- `path=""` means mount at the module root, such as `/account`;
- `path="/callback"` means absolute path and bypasses the module mount point.

`Route(name=...)` is also an escape hatch. Ordinary routes should not repeat
their key in a name field.

## Module Mounting

Application composition continues to declare module mounts in `app.toml`:

```toml
[routes]
"wevra.auth" = "/account"
```

Composition applies that mount only to relative route paths. With the route
table above:

```text
auth:account        -> /account
auth:login          -> /account/login
auth:signup         -> /account/signup
auth:logout         -> /account/logout
auth:password-reset -> /account/password/reset
```

Absolute route paths bypass the mount point and should be used only for special
cases that are intentionally global.

## View And Handler Model

`Route(...)` accepts a route target. Supported targets should include:

- a `View` class;
- a view instance;
- a view factory;
- a plain sync or async function whose first required argument is `request`.

Route declaration stores the target but does not construct class or factory
targets during import. The dispatcher resolves or constructs the target lazily.
The default can be a first-use singleton for stateless views, with a factory
escape hatch for per-dispatch construction if a later requirement needs it.

Class-based views should follow a Django-style dispatch model:

```python
class LoginView(TemplateView):
    http_method_names = (HttpMethod.GET, HttpMethod.HEAD, HttpMethod.POST)

    async def get(self, request: Request) -> Response:
        ...

    async def post(self, request: Request) -> Response:
        ...
```

The base view dispatch operation should:

1. normalise the request method;
2. verify it is in `http_method_names`;
3. locate the corresponding lower-case handler method;
4. return a method-not-allowed response when unsupported;
5. call the handler and normalise its result into a valid response.

Plain function handlers receive the same request and can use the same helpers:

```python
async def login(request: Request) -> Response:
    if method := can_handle(request, (HttpMethod.GET, HttpMethod.HEAD)):
        return await render_login(request)
    if method := can_handle(request, (HttpMethod.POST,)):
        return await submit_login(request)

    return invalid_method(
        request,
        (HttpMethod.GET, HttpMethod.HEAD, HttpMethod.POST),
    )
```

The route layer may optionally use explicit route metadata for FastAPI method
registration, but method validation remains owned by the handler/view contract.

## Method Helpers

`wevra.web` should expose reusable method primitives:

- `HttpMethod`, a constrained HTTP method representation;
- `can_handle(request, methods) -> HttpMethod | None`;
- `invalid_method(request, methods) -> Response`.

The helpers should be usable by both class-based views and plain functions. The
`Allow` header produced by method-not-allowed responses must reflect the
declared allowed methods.

## Reverse URL Contract

Templates and handlers should use generated route names rather than hard-coded
paths. For auth, this change should move toward route names such as:

```text
auth:login
auth:signup
auth:logout
auth:account
auth:password-reset
auth:verify
```

Separate submit route names should disappear when GET and POST are method
handlers on the same logical route.

## Route Surfaces

The current page/partial/API distinction remains useful for validation and
error response selection, but it should not be represented as separate route
tables. A route may carry surface metadata, or a handler/view may expose it.

The dispatcher and validation should still be able to distinguish:

- full page responses;
- partial or htmx fragment responses;
- machine-oriented API responses.

## Exception Handling

`wevra.web` should provide a dispatcher-level exception handling boundary,
similar in role to Spring global exception handling. Exceptions raised by
class-based views or function handlers should flow through a global dispatcher
exception registry before a response is returned.

The exception handling boundary should:

- map known exceptions to responses by exception type and route surface;
- preserve HTTP status codes for HTTP exceptions;
- produce valid full-page error responses for page routes;
- produce fragment-compatible error responses for partial routes;
- produce machine-oriented responses for API routes;
- produce 405 responses with an `Allow` header for unsupported methods;
- allow host applications or framework modules to register specialised
  handlers without importing the host application from `wevra.web`.

FastAPI or Starlette app-level exception handlers may remain as a fallback for
raw FastAPI routers and non-dispatcher errors, but routes declared through
`ModuleRoutes` should receive top-level dispatcher exception handling.

## Migration Strategy

1. Introduce the new route/view primitives in `wevra.web` beside the current
   implementation.
2. Add tests for declarative route maps, method dispatch, function handlers,
   lazy view construction, relative/absolute path composition, root route
   mounting, reverse URL names, and dispatcher exception mapping.
3. Convert `wevra.web` built-in routes to the new route map.
4. Convert `wevra.auth` pages from split `identity:*` page/submit routes to
   method-dispatching `auth:*` logical routes.
5. Convert `uniquode` public and health routes where appropriate.
6. Update validation so route-map declarations are checked before startup.
7. Remove or deprecate the old `HtmlRouteDefinition` and split route-bucket
   API once all live modules have moved.

## Open Questions

- Should a route target function without explicit method metadata register a
  broad method set by default, or should it default to `GET` and require
  metadata for broader handling?
- Should lazy class-based views be cached as singletons by default, or should
  `Route(...)` make singleton/per-request construction explicit?
- Should route surface default to `page`, be inferred from path prefixes such
  as `/api` and `/partials`, or be mandatory for non-page routes?
