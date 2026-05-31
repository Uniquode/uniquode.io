## ADDED Requirements

### Requirement: Explicit module web inclusion
The system SHALL discover reusable module web surfaces through an explicit
application-owned list of enabled route modules rather than by scanning installed
packages or implicitly importing conventional module names.

#### Scenario: Enabled module list is deterministic
- **WHEN** the application starts with enabled route modules configured
- **THEN** the web composition layer imports those modules in configured order
  and uses that order for route registration, template fallback precedence, and
  context-provider defaults

#### Scenario: Unlisted module is not mounted
- **WHEN** a package is installed but is not present in the enabled route module
  list
- **THEN** the application does not register its routes, package templates, or
  context providers

#### Scenario: Missing module fails clearly
- **WHEN** an enabled route module cannot be imported
- **THEN** application startup or validation fails with a configuration error
  that names the missing module

### Requirement: Module route export convention
The system SHALL use a `module_routes` export as the conventional route-module
interface for publishing module web resources.

#### Scenario: Module publishes web resources
- **WHEN** a route module exposes `module_routes`
- **THEN** that object describes the module's page routes, partial routes, API
  routers, template packages, and template-context provider import names

#### Scenario: Module omits unused resource types
- **WHEN** a route module has no page routes, partial routes, API routers,
  template packages, or context providers
- **THEN** the missing elements are treated as empty collections so the
  application can back-fill defaults without special-case module code

#### Scenario: Malformed export fails validation
- **WHEN** an enabled route module exposes a malformed `module_routes` value
- **THEN** application startup or validation fails before any partial route set
  is registered

### Requirement: Web route surfaces remain separated
The system SHALL keep page routes, partial routes, and API routers as separate
module route surfaces.

#### Scenario: Page route binds to page view
- **WHEN** a module declares a page route
- **THEN** the route definition binds route metadata to a view that renders a
  full HTML page response

#### Scenario: Partial route binds to fragment view
- **WHEN** a module declares a partial route
- **THEN** the route definition binds route metadata to a view that renders an
  HTML fragment response suitable for partial-page interactions

#### Scenario: API route remains API router
- **WHEN** a module declares machine-oriented endpoints
- **THEN** those endpoints are published through FastAPI API routers rather than
  through the HTML page or partial dispatcher

### Requirement: Logical template namespace
The system SHALL render templates from a single logical namespace backed by an
application template root and enabled module package template sources.

#### Scenario: Application template overrides package template
- **WHEN** both the application template root and an enabled module package
  provide the same logical template path
- **THEN** the renderer uses the application template and stops searching later
  sources

#### Scenario: Module templates are searched in configured order
- **WHEN** multiple enabled modules provide the same logical template path and
  the application does not provide an override
- **THEN** the renderer uses the first matching module template according to the
  enabled route module order

#### Scenario: Missing template fails normally
- **WHEN** no configured template source provides a requested logical template
  path
- **THEN** rendering fails with the standard template-not-found behaviour for
  the renderer

### Requirement: Configurable template reload and cache policy
The system SHALL make Jinja2 template reload and cache behaviour configurable
for development and production use.

#### Scenario: Local development can reload templates
- **WHEN** template auto-reload is enabled and the template cache is disabled or
  minimised
- **THEN** template edits are visible without restarting the application where
  the underlying template source exposes file changes

#### Scenario: Production can cache templates
- **WHEN** template auto-reload is disabled and a positive cache size is
  configured
- **THEN** the renderer reuses cached compiled templates according to the Jinja2
  environment configuration

### Requirement: Template context provider pipeline
The system SHALL build template context through an async provider pipeline whose
providers are configured by import name and resolved once at application
startup.

#### Scenario: Module publishes context provider names
- **WHEN** an enabled route module declares context provider import names
- **THEN** the application can include those providers in the request-time
  context pipeline after applying configured additions, removals, replacements,
  or reordering

#### Scenario: Provider is resolved before requests
- **WHEN** the application starts
- **THEN** context provider import names are resolved to async callables and
  invalid providers fail startup or validation

#### Scenario: Provider contributes request context
- **WHEN** a page or partial view is rendered
- **THEN** each configured provider receives the request and returns context
  values that are merged before view-local context is applied

#### Scenario: Reserved context keys are protected
- **WHEN** a context provider or view attempts to override reserved internal
  keys such as `request`, `route_name`, or CSRF fields
- **THEN** rendering fails before a response is returned

### Requirement: Module web validation
The system SHALL validate enabled module web configuration before runtime
failures are left to ordinary requests.

#### Scenario: Validation checks enabled modules
- **WHEN** the web validation command runs
- **THEN** it inspects the enabled route modules, `module_routes` exports,
  registered route surfaces, template package sources, and context provider
  import names

#### Scenario: Validation detects broken template references
- **WHEN** an enabled page or partial route references a logical template path
  that cannot be resolved through the configured template sources
- **THEN** validation reports the broken reference

#### Scenario: Validation detects conflicting route definitions
- **WHEN** enabled modules define conflicting route names or method/path pairs
- **THEN** validation reports the conflict before the application relies on
  route-order side effects
