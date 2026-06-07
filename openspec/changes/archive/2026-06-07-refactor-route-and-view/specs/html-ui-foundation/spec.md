## ADDED Requirements

### Requirement: Module routes use FastAPI routers
The system SHALL compose module-owned FastAPI routers from explicitly
configured application modules.

#### Scenario: Module route surface exposes router labels
- **WHEN** a configured module exposes its route surface
- **THEN** `<module>.routes` exposes `module_routers` as a mapping from stable
  router labels to FastAPI `APIRouter` instances

#### Scenario: Application config maps router labels to prefixes
- **WHEN** application composition config declares route prefixes
- **THEN** each configured module maps router labels to FastAPI include
  prefixes

#### Scenario: Router prefix is applied at inclusion
- **WHEN** Wevra composes configured module routers
- **THEN** it calls FastAPI router inclusion with the configured prefix for each
  router label

#### Scenario: Router paths remain FastAPI paths
- **WHEN** a module declares a route on an `APIRouter`
- **THEN** the route path begins with `/` and is interpreted using normal
  FastAPI path semantics

#### Scenario: Root-mounted router is explicit
- **WHEN** a configured router should register routes at the application root
- **THEN** the application configures that router label with an empty prefix

#### Scenario: Prefixed router does not support absolute bypass
- **WHEN** a router is included with a non-empty prefix
- **THEN** all routes declared on that router are mounted beneath the prefix
- **AND** any route that should bypass that prefix is declared on a separate
  router mounted with an empty or different prefix

#### Scenario: Handler decorators register routes
- **WHEN** module handlers use `@router.get`, `@router.post`, or
  `@router.api_route`
- **THEN** route registration follows FastAPI decorator semantics at import
  time

#### Scenario: Route module loads decorated handlers
- **WHEN** decorated handlers live outside `<module>.routes`
- **THEN** `<module>.routes` imports the handler modules before exposing the
  routers for application inclusion

#### Scenario: FastAPI parameter handling is preserved
- **WHEN** a route handler declares path, query, body, form, dependency, or
  `Request` parameters
- **THEN** FastAPI performs its normal parameter extraction and validation

#### Scenario: Reverse URL names are FastAPI names
- **WHEN** templates or handlers link to a module route
- **THEN** they use the FastAPI/Starlette route name declared on the route
  decorator rather than a Wevra-generated route name

### Requirement: HTML form protection remains enforced
The system SHALL preserve CSRF protection for unsafe HTML form submissions after
moving route declaration to FastAPI routers.

#### Scenario: Unsafe form submission validates CSRF
- **WHEN** an unsafe HTTP method submits an HTML form to a protected route
- **THEN** the request is rejected unless it carries a valid CSRF token

#### Scenario: Safe requests do not require CSRF
- **WHEN** a safe HTTP method requests an HTML page or fragment
- **THEN** the request does not require a submitted CSRF token

#### Scenario: CSRF integration uses FastAPI-compatible hooks
- **WHEN** modules attach CSRF protection to routes
- **THEN** they use FastAPI-compatible dependencies, router configuration, or
  helper functions rather than a custom dispatcher-only hook

### Requirement: Cross-origin opener policy is configurable
The system SHALL provide configurable `Cross-Origin-Opener-Policy` response
headers for browser isolation and popup-oriented flows.

#### Scenario: Default opener policy is applied
- **WHEN** a browser receives a normal application response
- **THEN** the response includes the configured default
  `Cross-Origin-Opener-Policy` header unless that default is explicitly
  disabled

#### Scenario: Popup route can relax opener policy
- **WHEN** a route or router is configured for a popup-oriented flow such as
  OAuth or payment handling
- **THEN** that response can use a route-specific opener policy such as
  `same-origin-allow-popups` without changing the application-wide default

#### Scenario: Existing explicit header is preserved
- **WHEN** a handler deliberately sets `Cross-Origin-Opener-Policy` on its
  response
- **THEN** the framework-level opener-policy support does not overwrite that
  explicit response header

#### Scenario: Opener policy uses FastAPI-compatible hooks
- **WHEN** a route needs a policy override
- **THEN** it can express that override through FastAPI/Starlette-compatible
  middleware, endpoint metadata, route metadata, dependency, or helper
  mechanisms rather than through a custom dispatcher

## MODIFIED Requirements

### Requirement: HTML route surfaces are explicit
The system SHALL keep page routes, partial routes, and API routes distinguishable
for rendering, validation, CSRF, and exception-response selection while using
FastAPI routers as the route declaration mechanism.

#### Scenario: Page route renders a full template
- **WHEN** a browser requests a page route
- **THEN** the handler returns a full HTML page response rendered from the
  template system or another valid page response

#### Scenario: Partial route renders a fragment
- **WHEN** a browser requests a partial route intended for `htmx`
- **THEN** the handler returns an HTML fragment response rather than a full page
  shell

#### Scenario: API route stays machine-oriented
- **WHEN** a client requests an API route
- **THEN** the handler returns a machine-oriented response rather than a
  template-rendered HTML page

#### Scenario: Route surface uses FastAPI-compatible metadata
- **WHEN** a module declares routes
- **THEN** page, partial, and API surface information is represented through
  FastAPI-compatible router, route, dependency, tag, or endpoint metadata rather
  than a custom dispatcher-only route table

### Requirement: Error handling is explicit across route surfaces
The system SHALL provide explicit error-handling behaviour for page, partial,
and API route surfaces using FastAPI/Starlette exception-handler mechanisms and
Wevra response helpers.

#### Scenario: FastAPI route exceptions are handled
- **WHEN** a module route handler raises an exception
- **THEN** the application passes the exception through configured
  FastAPI/Starlette exception handlers before returning a response

#### Scenario: Page route `404` renders an HTML error page
- **WHEN** a browser requests a missing page route or a page route raises a
  not-found exception
- **THEN** the application returns an HTML `404` response rendered through the
  shared error-template foundation

#### Scenario: Page route `500` renders an HTML error page
- **WHEN** an unhandled server error occurs while serving a page route
- **THEN** the application returns an HTML `500` response rendered through the
  shared error-template foundation

#### Scenario: API route errors remain machine-oriented regardless of `Accept`
- **WHEN** a client requests an API route and the request fails
- **THEN** the application returns a machine-oriented error response rather than
  a template-rendered HTML page, even if the caller sends `Accept: text/html`
  or other browser-like headers

#### Scenario: Partial-route errors remain fragment-compatible
- **WHEN** a request intended for a partial or `htmx` fragment fails
- **THEN** the application returns an HTML error response that remains
  compatible with fragment-oriented clients rather than replacing the
  interaction with an unrelated full page

#### Scenario: Unsupported methods return `405`
- **WHEN** a route handler does not support the request method
- **THEN** FastAPI/Starlette returns `405 Method Not Allowed` and the `Allow`
  header lists the supported methods

#### Scenario: Exception handlers are extensible without host imports
- **WHEN** a framework module or host application needs specialised exception
  mapping
- **THEN** it can register exception handlers without `wevra.web` importing the
  host application package

## REMOVED Requirements

### Requirement: HTML requests use a dispatcher protocol
**Reason**: Route declaration and request dispatch now use FastAPI routers and
FastAPI/Starlette handler dispatch directly.

**Migration**: Modules expose labelled `module_routers` from `<module>.routes`;
handlers register with FastAPI decorators, and route-surface information is
represented through FastAPI-compatible metadata.
