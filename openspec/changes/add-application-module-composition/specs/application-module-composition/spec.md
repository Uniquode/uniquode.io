## ADDED Requirements

### Requirement: Shared composition configuration
The system SHALL load application composition from a shared `app.toml`
configuration file that can be consumed by runtime startup, Alembic,
validation, static-asset export, and future CLIs without importing
application-runtime state.

#### Scenario: Default app configuration file is used
- **WHEN** no composition configuration override is supplied
- **THEN** the composition loader reads `app.toml` from the application
  configuration root

#### Scenario: APP_CONFIG overrides app configuration path
- **WHEN** `APP_CONFIG` is set to a configuration file path
- **THEN** runtime startup, Alembic, validation, static export, and future CLIs
  read composition from that file path

#### Scenario: Runtime consumes shared composition configuration
- **WHEN** the web application starts
- **THEN** runtime settings adapt the shared composition configuration rather
  than owning a separate installed-module source of truth

#### Scenario: Alembic consumes shared composition configuration
- **WHEN** migration metadata loading runs
- **THEN** it reads installed modules through the shared composition loader
  without importing FastAPI application startup code

#### Scenario: CLI consumes shared composition configuration
- **WHEN** a project CLI needs installed modules or resource sources
- **THEN** it can load the shared composition configuration without importing
  the application FastAPI startup path, Jinja environment, route modules, or
  `auth_ext`

#### Scenario: Auth configuration remains separate by default
- **WHEN** auth configuration is loaded during this change
- **THEN** the existing default `auth.toml` behaviour remains available while
  `app.toml` can later reserve compatible directives for a separate
  configuration-unification change

#### Scenario: Composition configuration rejects runtime-only settings
- **WHEN** the composition configuration is parsed
- **THEN** secrets, deployment-only values, and product policy settings are
  outside the composition schema

### Requirement: Explicit installed module composition
The system SHALL compose application modules from an ordered `installed_modules`
list loaded from shared composition configuration rather than by scanning
installed packages or implicitly importing conventional module names.

#### Scenario: Installed module list is deterministic
- **WHEN** the application starts with installed modules configured
- **THEN** the composition layer imports those modules in configured order
  and uses that order as the basis for model metadata loading, route
  registration, template/static fallback precedence, and context-provider
  defaults

#### Scenario: Unlisted module contributes nothing
- **WHEN** a package is installed but is not present in `installed_modules`
- **THEN** the application does not load its model metadata, routes, package
  templates, package static assets, or context providers

#### Scenario: Missing installed module fails clearly
- **WHEN** a configured installed module cannot be imported
- **THEN** application startup, migration metadata loading, or validation fails
  with a configuration error that names the missing module

#### Scenario: Auth extension can be omitted
- **WHEN** `auth_ext` is not present in `installed_modules`
- **THEN** the application does not load auth extension model metadata, routes,
  package templates, package static assets, context providers, or
  identity-specific startup wiring

### Requirement: Optional module surface conventions
The system SHALL allow installed modules to contribute optional application
surfaces through conventional module/package locations.

#### Scenario: Module publishes optional surfaces
- **WHEN** an installed module provides conventional model, route, template,
  static, or context-provider surfaces
- **THEN** the composition layer includes those surfaces according to the
  application composition configuration

#### Scenario: Module omits unused surfaces
- **WHEN** an installed module does not provide models, routes, templates,
  static assets, or context providers
- **THEN** the missing surfaces are treated as empty contributions rather than
  startup errors

#### Scenario: Malformed surface fails validation
- **WHEN** an installed module exposes malformed model metadata, route exports,
  template/static source declarations, or context-provider names
- **THEN** application startup or validation fails before any partial
  application surface is registered

#### Scenario: Resource surfaces do not require route imports
- **WHEN** validation or static-asset export needs package template or static
  sources
- **THEN** it discovers those sources from installed modules without importing
  module route exports

### Requirement: `web_ext` core layer
The system SHALL keep shared configuration, composition contracts, resource
resolution, context-provider registry contracts, and static export services in
the top-level `web_ext` package.

#### Scenario: Core layer avoids application imports
- **WHEN** `web_ext` is imported
- **THEN** it does not import product routes, product settings, `uniquode.app`,
  `auth_ext`, application FastAPI startup, or deployment secrets

#### Scenario: Core layer may use FastAPI engine contracts
- **WHEN** `web_ext` defines routing or request/response contracts
- **THEN** it may depend on FastAPI and Starlette APIs already present in the
  project without depending on a concrete application instance

#### Scenario: Application consumes core layer
- **WHEN** the `uniquode` application starts
- **THEN** it uses `web_ext` for composition loading, route/resource
  contracts, template/static source resolution, and context-provider wiring

#### Scenario: Tools consume core layer
- **WHEN** Alembic, validation, static export, or future CLIs need composition
  information
- **THEN** they call `web_ext` rather than duplicating installed-module
  defaults or importing the web application

#### Scenario: Auth extension consumes core contracts
- **WHEN** `auth_ext` publishes identity module surfaces
- **THEN** it may depend on `web_ext` contracts while `web_ext` remains
  independent of `auth_ext`

### Requirement: Module model metadata loading
The system SHALL derive SQLAlchemy model metadata loading from installed modules
that expose model metadata.

#### Scenario: Module models expose metadata
- **WHEN** an installed module has a conventional models surface with top-level
  SQLAlchemy `metadata`
- **THEN** migration metadata loading includes that metadata in installed module
  order

#### Scenario: Module without models is skipped
- **WHEN** an installed module has no conventional models surface
- **THEN** migration metadata loading skips that module without failing

#### Scenario: Invalid model metadata fails clearly
- **WHEN** an installed module's models surface exists but does not expose
  SQLAlchemy `metadata`
- **THEN** migration metadata loading fails with a clear error that names the
  offending module

### Requirement: Module route export convention
The system SHALL use a `module_routes` export as the conventional route-module
interface for publishing module web resources.

#### Scenario: Module publishes web resources
- **WHEN** an installed module exposes `module_routes`
- **THEN** that object describes the module's page routes, partial routes, API
  routers, and template-context provider import names

#### Scenario: Relative routes use configured module prefix
- **WHEN** a module route path is relative
- **THEN** the application mounts that route below the configured route prefix
  for that module

#### Scenario: Absolute routes keep declared path
- **WHEN** a module route path starts with `/`
- **THEN** the application registers that route at the declared absolute path
  rather than applying the module route prefix

#### Scenario: Route conflicts fail composition
- **WHEN** installed modules define conflicting route names or method/path
  pairs after prefix resolution
- **THEN** validation or startup reports the conflict before route-order side
  effects can determine behaviour

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
application template root and installed module package template sources.

#### Scenario: Application template overrides package template
- **WHEN** both the application template root and an installed module package
  provide the same logical template path
- **THEN** the renderer uses the application template and stops searching later
  sources

#### Scenario: Module templates use deterministic precedence
- **WHEN** multiple installed modules provide the same logical template path and
  the application does not provide an override
- **THEN** the renderer uses the first matching module template according to
  reverse installed module order

#### Scenario: Missing template fails normally
- **WHEN** no configured template source provides a requested logical template
  path
- **THEN** rendering fails with the standard template-not-found behaviour for
  the renderer

### Requirement: Logical static asset namespace
The system SHALL serve static assets from a single logical namespace backed by
an application static root and installed module package static sources.

#### Scenario: Application static asset overrides package asset
- **WHEN** both the application static root and an installed module package
  provide the same logical static asset path
- **THEN** the static asset resolver serves the application asset and stops
  searching later sources

#### Scenario: Module static assets use deterministic precedence
- **WHEN** multiple installed modules provide the same logical static asset path
  and the application does not provide an override
- **THEN** the resolver serves the first matching module asset according to
  reverse installed module order

#### Scenario: Missing static asset fails normally
- **WHEN** no configured static source provides a requested logical asset path
- **THEN** the static route returns the framework's normal missing-asset
  response

### Requirement: Static asset export boundary
The system SHALL provide a collectstatic-style service boundary that exports
the composed logical static namespace into a filesystem directory without
booting the web application.

#### Scenario: Static export uses runtime precedence
- **WHEN** static export runs
- **THEN** it enumerates the application static root and installed module
  package static sources using the same precedence as runtime static serving

#### Scenario: Static export writes winning assets
- **WHEN** multiple static sources provide the same logical static path
- **THEN** static export writes only the winning asset for that logical path to
  the export directory

#### Scenario: Static export avoids web startup
- **WHEN** static export loads composition and static sources
- **THEN** it does not import application FastAPI startup code, route modules,
  the Jinja environment, or identity-specific runtime state

#### Scenario: Static export belongs to web extension core
- **WHEN** static export is implemented
- **THEN** it is exposed by `web_ext` rather than by `auth_ext`

#### Scenario: Static export reports duplicate defaults
- **WHEN** installed module package static sources provide duplicate logical
  paths
- **THEN** static export reports those duplicates consistently with validation

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
- **WHEN** an installed module declares context provider import names
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

#### Scenario: Provider key collisions fail by default
- **WHEN** two context providers contribute the same non-reserved context key
  without an explicit override policy
- **THEN** rendering fails before a response is returned

### Requirement: Application composition validation
The system SHALL validate installed module composition before runtime failures
are left to ordinary requests.

#### Scenario: Validation checks installed modules
- **WHEN** the validation command runs
- **THEN** it inspects installed modules, optional module surfaces, route
  exports, model metadata, package template sources, package static sources,
  and context provider import names

#### Scenario: Validation detects broken template references
- **WHEN** an enabled page or partial route references a logical template path
  that cannot be resolved through configured template sources
- **THEN** validation reports the broken reference

#### Scenario: Validation detects broken static references
- **WHEN** an implemented template or module surface references a logical static
  asset path that cannot be resolved through configured static sources
- **THEN** validation reports the broken reference where the reference is
  statically inspectable

#### Scenario: Validation detects conflicting route definitions
- **WHEN** installed modules define conflicting route names or method/path pairs
- **THEN** validation reports the conflict before the application relies on
  route-order side effects
