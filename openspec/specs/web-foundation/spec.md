# web-foundation Specification

## Purpose
Define the baseline web foundation for server-rendered pages, shared templates, semantic theming, and progressive enhancement in the `uniquode` application.
## Requirements
### Requirement: Module-owned web resources
The system SHALL load template and static resources from configured modules
while keeping global template behaviour and static serving/export options in
composition configuration.

#### Scenario: Template behaviour has global configuration
- **WHEN** a developer inspects the project composition configuration
- **THEN** the application defines configurable Jinja2 template reload and cache
  behaviour without requiring a global filesystem template root

#### Scenario: Configured modules can add package template sources
- **WHEN** the application installs modules that declare package templates
- **THEN** the renderer includes those package template sources according to
  configured module order

#### Scenario: Static serving and export have global configuration
- **WHEN** a developer inspects the project composition or static asset
  configuration
- **THEN** the application defines a configurable static URL path and static
  export root without requiring a global filesystem static root

#### Scenario: Configured modules can add package static sources
- **WHEN** the application installs modules that declare package static assets
- **THEN** the static asset resolver includes those package static sources
  according to configured module order

#### Scenario: Static route prefix has a settings-backed default
- **WHEN** a developer inspects the project settings or static asset configuration
- **THEN** the application defines a configurable static route prefix with a default value of `/static/`

### Requirement: Template hierarchy and reusable components
The system SHALL provide a baseline template hierarchy and reusable server-rendered component structure for HTML pages.

#### Scenario: Base template hierarchy exists
- **WHEN** a developer inspects the initial template set
- **THEN** it includes a ubiquitous base page template and a base HTML error template

#### Scenario: Shared components have a conventional location
- **WHEN** a developer inspects the template tree
- **THEN** shared reusable components live under the logical path `components/`

#### Scenario: Module-local components are supported
- **WHEN** a feature module introduces reusable templates that are primarily local to that module
- **THEN** the module can publish those templates from its package template
  source under logical paths such as `<module-base>/components/`

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

### Requirement: Static asset serving is separate from HTML route handling
The system SHALL keep static asset serving separate from HTML route handling.

#### Scenario: Static request uses static-serving path
- **WHEN** a client requests a path under the configured static URL prefix
- **THEN** the request is handled by the configured static-serving mechanism
  rather than by HTML route handlers

#### Scenario: Static URL contract supports production offload
- **WHEN** production infrastructure serves static assets directly
- **THEN** the configured static URL prefix remains valid without requiring
  HTML route handlers to serve those asset bytes

### Requirement: Baseline UI assets are delivered without a front-end build pipeline
The system SHALL provide the initial CSS and dynamic-enhancement baseline without requiring npm or another front-end build step.

#### Scenario: Pico CSS is available for MVP
- **WHEN** a rendered page loads the baseline stylesheet
- **THEN** Pico CSS is provided through the configured lightweight delivery approach for MVP

#### Scenario: htmx is available for progressive enhancement
- **WHEN** a rendered page uses `htmx` behaviour
- **THEN** the client receives `htmx` without requiring a front-end build pipeline

#### Scenario: Project CSS remains separate
- **WHEN** the application adds project-specific styles
- **THEN** those styles are layered separately from the baseline Pico CSS resource

### Requirement: Theme-aware styling is semantic across templates
The system SHALL apply theme-aware styling through semantic design roles and
tokens across the HTML foundation rather than through template-local light or
dark colour assumptions. The HTML foundation SHALL own semantic theme behaviour
and token expectations, while optional theme-selection UI belongs to composed UI
support modules such as `wevra.widgets`.

#### Scenario: Base templates consume semantic styling roles
- **WHEN** a developer inspects the base page templates and shared components
- **THEN** they rely on semantic styling roles such as background, surface, text, muted text, border, and accent rather than hard-coded mode-specific colour choices in template markup

#### Scenario: Theme mode changes token values rather than template structure
- **WHEN** the active theme mode changes between `auto`, `light`, and `dark`
- **THEN** the visual change is achieved by changing semantic token values and inherited styling rather than by branching the template structure per mode

#### Scenario: Project CSS defines mode-aware semantic tokens
- **WHEN** a developer inspects the project-specific stylesheet layer
- **THEN** the stylesheet defines semantic theme tokens or equivalent variables that support `auto`, `light`, and `dark` behaviour for the shared HTML foundation

#### Scenario: Theme selector UI is not owned by the web foundation
- **WHEN** a developer inspects the low-level web foundation templates and routes
- **THEN** the optional `auto`/`light`/`dark` selector UI is not implemented as a core `wevra.web` concern
- **AND** selector UI behaviour is provided by a composed UI support module when enabled

### Requirement: Web-structure validation is available
The system SHALL provide an initial validation surface for the web foundation that can detect structural errors before runtime.

#### Scenario: Validation command checks implemented web structure
- **WHEN** a developer runs the documented web-structure validation command
- **THEN** the command inspects implemented route, template, static asset,
  configured module, package template, package static, and
  template-context-provider structures and reports detected errors

#### Scenario: Web validation is contributed by web core
- **WHEN** web-structure validation is discovered
- **THEN** reusable web checks are contributed by `wevra.web.validation` rather
  than by the host application package

#### Scenario: Broken references fail validation
- **WHEN** an implemented route, template reference, package template
  reference, static asset reference, context provider reference, or module
  surface reference cannot be resolved by the validation surface
- **THEN** the validation command reports the failure instead of silently succeeding

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

### Requirement: Known and non-standard HTTP status codes have defined fallback behaviour
The system SHALL define fallback behaviour for both known HTTP status codes and
non-standard or application-specific termination-style status codes.

#### Scenario: Known HTTP status code uses generic fallback behaviour
- **WHEN** a request fails with a known HTTP status code that does not yet have a
  bespoke handler
- **THEN** the application uses a generic fallback representation that matches the
  current route surface rather than failing back to inconsistent framework defaults

#### Scenario: Non-standard termination-style status code bypasses generic rendering
- **WHEN** application policy selects a non-standard or termination-style status code
  such as `444`
- **THEN** the application bypasses generic HTML and JSON error rendering and uses
  the explicit empty-body or termination-style policy for that response path

### Requirement: Error handling fails closed and preserves only applicable metadata
The system SHALL harden error handling so it does not fall through to
non-applicable defaults or leak response metadata that is not explicitly safe to
propagate.

#### Scenario: Error translation preserves only safe response headers
- **WHEN** exception-derived headers are applied to an error response
- **THEN** the application preserves only explicitly safe headers needed for the
  error contract, such as authentication or retry metadata, rather than blindly
  copying all response headers

#### Scenario: Route-surface prefixes are validated before use
- **WHEN** route-surface prefixes are defined for API or partial detection
- **THEN** the application rejects empty or root-mounted prefixes so all requests
  cannot be silently classified as the same surface

#### Scenario: Rendering misconfiguration falls back to minimal safe responses
- **WHEN** HTML rendering infrastructure is unavailable or misconfigured during
  error handling
- **THEN** the application falls back to a minimal safe response for the current
  surface instead of recursing through the same rendering-dependent error path

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
