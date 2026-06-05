# html-ui-foundation Specification

## Purpose
Define the baseline HTML-first UI foundation for server-rendered pages, shared templates, semantic theming, and progressive enhancement in the `uniquode` application.

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
The system SHALL keep page routes, partial routes, and API routes as distinct route surfaces.

#### Scenario: Page route renders a full template
- **WHEN** a browser requests a page route
- **THEN** the handler returns a full HTML page response rendered from the template system

#### Scenario: Partial route renders a fragment
- **WHEN** a browser requests a partial route intended for `htmx`
- **THEN** the handler returns an HTML fragment response rather than a full page shell

#### Scenario: API route stays machine-oriented
- **WHEN** a client requests a route under `/api/`
- **THEN** the handler returns a machine-oriented response rather than a template-rendered HTML page

### Requirement: HTML requests use a dispatcher protocol
The system SHALL provide an internal HTML request-dispatch layer under FastAPI
for page-oriented handlers, with route definitions composed from explicitly
installed application modules.

#### Scenario: HTML views register declaratively
- **WHEN** a developer adds a page-oriented HTML view
- **THEN** the view registers through the HTML dispatcher mechanism rather than requiring a one-route-per-page decorator pattern

#### Scenario: Route definitions are declared in feature modules
- **WHEN** a feature module declares page or partial routes
- **THEN** the module exposes declarative route definitions through its route
  module rather than requiring the application to duplicate each route

#### Scenario: Application installs feature module routes explicitly
- **WHEN** the application includes a module in `modules`
- **THEN** the dispatcher registers that module's page and partial routes in
  configured order

#### Scenario: Dispatcher selects a matching view
- **WHEN** an HTML request reaches the dispatcher entry point
- **THEN** the dispatcher evaluates the registered HTML views against the request and selects the final view deterministically

#### Scenario: Selected view serves the response
- **WHEN** the dispatcher has selected an HTML view
- **THEN** it passes the full request to that view's serving operation and returns the resulting response

### Requirement: Static asset serving is separate from HTML dispatch
The system SHALL keep static asset serving separate from the HTML dispatcher.

#### Scenario: Static request uses static-serving path
- **WHEN** a client requests a path under the configured static URL prefix
- **THEN** the request is handled by the configured static-serving mechanism rather than by the HTML dispatcher

#### Scenario: Static URL contract supports production offload
- **WHEN** production infrastructure serves static assets directly
- **THEN** the configured static URL prefix remains valid without requiring the HTML dispatcher to serve those asset bytes

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
The system SHALL apply theme-aware styling through semantic design roles and tokens across the HTML foundation rather than through template-local light or dark colour assumptions.

#### Scenario: Base templates consume semantic styling roles
- **WHEN** a developer inspects the base page templates and shared components
- **THEN** they rely on semantic styling roles such as background, surface, text, muted text, border, and accent rather than hard-coded mode-specific colour choices in template markup

#### Scenario: Theme mode changes token values rather than template structure
- **WHEN** the active theme mode changes between `auto`, `light`, and `dark`
- **THEN** the visual change is achieved by changing semantic token values and inherited styling rather than by branching the template structure per mode

#### Scenario: Project CSS defines mode-aware semantic tokens
- **WHEN** a developer inspects the project-specific stylesheet layer
- **THEN** the stylesheet defines semantic theme tokens or equivalent variables that support `auto`, `light`, and `dark` behaviour for the shared HTML foundation

### Requirement: Web-structure validation is available
The system SHALL provide an initial validation surface for the web foundation that can detect structural errors before runtime.

#### Scenario: Validation command checks implemented web structure
- **WHEN** a developer runs the documented web-structure validation command
- **THEN** the command inspects implemented route, template, static asset,
  configured module, package template, package static, and
  template-context-provider structures and reports detected errors

#### Scenario: Web validation is contributed by web core
- **WHEN** web-structure validation is discovered
- **THEN** reusable web checks are contributed by `web_core.validation` rather
  than by the host application package

#### Scenario: Broken references fail validation
- **WHEN** an implemented route, template reference, package template
  reference, static asset reference, context provider reference, or module
  surface reference cannot be resolved by the validation surface
- **THEN** the validation command reports the failure instead of silently succeeding

### Requirement: Error handling is explicit across route surfaces
The system SHALL provide explicit error-handling behaviour for page, partial, and
API route surfaces rather than relying on framework defaults.

#### Scenario: Page route `404` renders an HTML error page
- **WHEN** a browser requests a missing page route
- **THEN** the application returns an HTML `404` response rendered through the
  shared error-template foundation

#### Scenario: Page route `500` renders an HTML error page
- **WHEN** an unhandled server error occurs while serving a page route
- **THEN** the application returns an HTML `500` response rendered through the
  shared error-template foundation

#### Scenario: API route errors remain machine-oriented regardless of `Accept`
- **WHEN** a client requests an API route and the request fails
- **THEN** the application returns a machine-oriented error response rather than a
  template-rendered HTML page, even if the caller sends `Accept: text/html`
  or other browser-like headers

#### Scenario: Partial-route errors remain fragment-compatible
- **WHEN** a request intended for a partial or `htmx` fragment fails
- **THEN** the application returns an HTML error response that remains compatible
  with fragment-oriented clients rather than replacing the interaction with an
  unrelated full-page shell

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
