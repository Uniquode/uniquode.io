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

#### Scenario: Root modules define configured modules
- **WHEN** `app.toml` contains a top-level `modules` list
- **THEN** the composition loader uses that list as the source for enabled
  modules

#### Scenario: Peer sections define route and resource options
- **WHEN** `app.toml` contains `[routes]`, `[templates]`, and `[static]` tables
- **THEN** the composition loader uses those tables for route prefixes,
  template options, static serving options, and static-export options

#### Scenario: APP_CONFIG overrides app configuration path
- **WHEN** `APP_CONFIG` is set to a configuration file path
- **THEN** runtime startup, Alembic, validation, static export, and future CLIs
  read composition from that file path

#### Scenario: Runtime consumes shared composition configuration
- **WHEN** the web application starts
- **THEN** runtime settings adapt the shared composition configuration rather
  than owning a separate module source of truth

#### Scenario: Settings loading mechanics are reusable
- **WHEN** an application uses the shared composition and envex-backed settings
  pattern
- **THEN** the reusable environment value parsing, app configuration loading,
  and settings factory invocation mechanics are provided by `web_core` while
  concrete settings fields and policy remain application-owned

#### Scenario: Alembic consumes shared composition configuration
- **WHEN** migration metadata loading runs
- **THEN** it reads configured modules through the shared composition loader
  without importing FastAPI application startup code

#### Scenario: CLI consumes shared composition configuration
- **WHEN** a project CLI needs configured modules or resource sources
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

### Requirement: Explicit module composition
The system SHALL compose application modules from an ordered `modules` list
loaded from shared composition configuration rather than by scanning
installed packages or implicitly importing conventional module names.

#### Scenario: Module list is deterministic
- **WHEN** the application starts with modules configured
- **THEN** the composition layer imports those modules in configured order
  and uses that order as the basis for model metadata loading, route
  registration, template/static fallback precedence, and context-provider
  defaults

#### Scenario: Unlisted module contributes nothing
- **WHEN** a package is installed but is not present in `modules`
- **THEN** the application does not load its model metadata, routes, package
  templates, package static assets, or context providers

#### Scenario: Missing configured module fails clearly
- **WHEN** a configured module cannot be imported
- **THEN** application startup, migration metadata loading, or validation fails
  with a configuration error that names the missing module

#### Scenario: Auth extension can be omitted
- **WHEN** `auth_ext` is not present in `modules`
- **THEN** the application does not load auth extension model metadata, routes,
  package templates, package static assets, context providers, or
  identity-specific startup wiring

### Requirement: Optional module surface conventions
The system SHALL allow configured modules to contribute optional application
surfaces through conventional module/package locations.

#### Scenario: Module publishes optional surfaces
- **WHEN** a configured module provides conventional model, route, template,
  static, context-provider, or validation surfaces
- **THEN** the composition layer includes those surfaces according to the
  application composition configuration

#### Scenario: Module omits unused surfaces
- **WHEN** a configured module does not provide models, routes, templates,
  static assets, context providers, or validation targets
- **THEN** the missing surfaces are treated as empty contributions rather than
  startup errors

#### Scenario: Malformed surface fails validation
- **WHEN** a configured module exposes malformed model metadata, route exports,
  template/static source declarations, or context-provider registrations
- **THEN** application startup or validation fails before any partial
  application surface is registered

#### Scenario: Resource surfaces do not require route imports
- **WHEN** validation or static-asset export needs package template or static
  sources
- **THEN** it discovers those sources from configured modules without importing
  module route exports

### Requirement: Module validation target discovery
The system SHALL run validation targets discovered from configured module
validation surfaces rather than from a hard-coded application-owned registry.

#### Scenario: Tools package owns validation orchestration
- **WHEN** a developer runs the `validate` console command
- **THEN** command orchestration, target discovery, shared validation result
  types, and output handling are provided by the top-level `tools` package

#### Scenario: Tools package owns runtime command orchestration
- **WHEN** a developer runs the `runserver` console command
- **THEN** local runtime command parsing and Uvicorn delegation are provided by
  the top-level `tools` package while the command still targets the configured
  project ASGI application

#### Scenario: Validation targets are discovered from configured modules
- **WHEN** configured modules expose conventional `<module>.validation`
  surfaces with a `validation_targets` mapping
- **THEN** the validation command iterates the configured module list and runs
  targets from those mappings in discovered order

#### Scenario: Missing validation surface is optional
- **WHEN** a configured module has no `<module>.validation` surface
- **THEN** the validation command treats that module as contributing no
  validation targets

#### Scenario: Unlisted module validation is ignored
- **WHEN** an installed module exposes a validation target but is not present in
  the configured module list
- **THEN** the validation command does not discover or run that target

#### Scenario: Malformed validation surface fails clearly
- **WHEN** a configured module exposes a malformed validation target mapping
- **THEN** validation fails before running checks and reports the offending
  validation surface

#### Scenario: Unknown requested target fails clearly
- **WHEN** a developer requests a validation target that no configured module
  contributed
- **THEN** the validation command exits with usage failure naming the unknown
  target

#### Scenario: Application-specific validation remains module-owned
- **WHEN** the `uniquode` module is configured
- **THEN** application-specific environment and persistence validation targets
  are contributed by `uniquode.validation`

### Requirement: `web_core` core layer
The system SHALL keep shared configuration, composition contracts, reusable
HTML runtime primitives, resource resolution, context-provider registry
contracts, reusable foundation resources, and static export services in the
top-level `web_core` package.

#### Scenario: Core layer avoids application imports
- **WHEN** `web_core` is imported
- **THEN** it does not import product routes, product settings, `uniquode.app`,
  `auth_ext`, application FastAPI startup, or deployment secrets

#### Scenario: Module surface conventions are centralised
- **WHEN** reusable layers need conventional configured-module surface names or
  export attribute names
- **THEN** those strings are defined in one reusable convention module rather
  than being duplicated across web, data, and tooling discovery code

#### Scenario: Core layer may use FastAPI engine contracts
- **WHEN** `web_core` defines routing or request/response contracts
- **THEN** it may depend on FastAPI and Starlette APIs already present in the
  project without depending on a concrete application instance

#### Scenario: Application consumes core layer
- **WHEN** the `uniquode` application starts
- **THEN** it uses `web_core` for composition loading, route/resource
  contracts, HTML dispatching, template rendering, CSRF/form security,
  generic error handling, template/static source resolution, and
  context-provider wiring

#### Scenario: Tools consume web core layer
- **WHEN** validation, static export, or future CLIs need web composition
  information
- **THEN** they call `web_core` rather than duplicating web module defaults or
  importing the web application

#### Scenario: Migrations consume data core layer
- **WHEN** Alembic or future data CLIs need model metadata or migration version
  locations
- **THEN** they call `data_core` rather than duplicating data module defaults or
  importing the web application

#### Scenario: Web validation belongs to core layer
- **WHEN** web-structure validation runs
- **THEN** reusable web route, template, static, context, CSRF, style, and theme
  checks are contributed by `web_core.validation` without importing the
  `uniquode` application package

#### Scenario: Auth extension consumes core contracts
- **WHEN** `auth_ext` publishes identity module surfaces
- **THEN** it may depend on `web_core` contracts while `web_core` remains
  independent of `auth_ext`

#### Scenario: Host application does not own reusable web runtime
- **WHEN** reusable page modules need HTML view, renderer, CSRF, form, route,
  theme, settings-loading, or default error/layout/static support
- **THEN** they import those reusable contracts or helpers from `web_core`
  rather than from the `uniquode` application package

#### Scenario: Host application does not own generic route registration
- **WHEN** the application registers configured module page, partial, and API
  routes
- **THEN** generic configured-module route loading, prefix handling, and
  registration helpers are provided by `web_core` rather than by the
  `uniquode` application package

### Requirement: Module model metadata loading
The system SHALL derive SQLAlchemy model metadata loading through `data_core`
from configured modules that expose model metadata.

#### Scenario: Data core owns reusable data contracts
- **WHEN** reusable SQLAlchemy model infrastructure is needed
- **THEN** the shared declarative base, database URL helpers, async
  engine/session helpers, and configured model metadata discovery helpers are
  provided by `data_core` rather than by `web_core` or the `uniquode`
  application package

#### Scenario: Database URL diagnostics redact secrets
- **WHEN** reusable data or validation code reports an effective database URL
- **THEN** authority credentials and sensitive query parameters such as
  passwords, tokens, keys, and secrets are redacted before output

#### Scenario: Module models expose metadata
- **WHEN** a configured module has a conventional `<module>.models` surface with top-level
  SQLAlchemy `metadata`
- **THEN** migration metadata loading includes that metadata in configured module
  order

#### Scenario: Module without models is skipped
- **WHEN** a configured module has no conventional `<module>.models` surface
- **THEN** migration metadata loading skips that module without failing

#### Scenario: Invalid model metadata fails clearly
- **WHEN** a configured module's `<module>.models` surface exists but does not expose
  SQLAlchemy `metadata`
- **THEN** migration metadata loading fails with a clear error that names the
  offending module

#### Scenario: Application without models contributes no metadata
- **WHEN** the configured `uniquode` application module does not define real
  application data models
- **THEN** it does not expose a placeholder model metadata surface

#### Scenario: Duplicate metadata objects are de-duplicated
- **WHEN** multiple configured model packages expose the same SQLAlchemy
  metadata object
- **THEN** migration metadata loading returns that metadata object once while
  preserving first-discovered module order

### Requirement: Module-owned migration history
The system SHALL keep migration command infrastructure in `data_core` while
allowing configured modules to own migration revision files for their models.

#### Scenario: Data core owns migration infrastructure
- **WHEN** a developer runs the project migration command
- **THEN** command orchestration, Alembic environment support, script template
  support, model metadata discovery, and migration version-location discovery
  are provided by `data_core`

#### Scenario: Host injects migration settings
- **WHEN** the project migration command needs application-specific settings,
  default modules, or the default database URL
- **THEN** those values are supplied by a host adapter or Alembic configuration
  options rather than by `data_core` importing the host application package

#### Scenario: Module owns revisions for its models
- **WHEN** a configured module owns SQLAlchemy tables
- **THEN** that module can provide migration revisions under a conventional
  module migration location

#### Scenario: Configured modules determine revision locations
- **WHEN** the migration command runs
- **THEN** Alembic version locations are derived from configured modules rather
  than from an application-owned global revisions directory

#### Scenario: Unlisted module revisions are ignored
- **WHEN** a module has migration revisions but is not present in the configured
  module list
- **THEN** those revisions are not included in the migration run

#### Scenario: Migration graph remains database-wide
- **WHEN** module-owned revision locations are composed
- **THEN** Alembic still applies them as one database-wide revision graph and
  the database records applied revisions in its version table

### Requirement: Module route export convention
The system SHALL use a `module_routes` export as the conventional route-module
interface for publishing module web resources.

#### Scenario: Module publishes web resources
- **WHEN** a configured module exposes `module_routes`
- **THEN** that object describes the module's page routes, partial routes, API
  routers, while context providers are discovered through the module's
  separate `<module>.context` surface

#### Scenario: Relative routes use configured module prefix
- **WHEN** a module route path is relative
- **THEN** the application mounts that route below the configured route prefix
  for that module

#### Scenario: Absolute routes keep declared path
- **WHEN** a module route path starts with `/`
- **THEN** the application registers that route at the declared absolute path
  rather than applying the module route prefix

#### Scenario: Route conflicts fail composition
- **WHEN** configured modules define conflicting route names or method/path
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
ordered configured module package template sources.

#### Scenario: Web core provides fallback templates
- **WHEN** `web_core` is included as the earliest configured module
- **THEN** it contributes reusable base layout, error, and theme component
  templates as low-precedence defaults

#### Scenario: Later module template overrides earlier module template
- **WHEN** multiple configured modules provide the same logical template path
- **THEN** the renderer uses the first matching module template according to
  reverse configured module order

#### Scenario: Module templates use deterministic precedence
- **WHEN** configured modules provide package template sources
- **THEN** the renderer uses the first matching module template according to
  reverse configured module order

#### Scenario: Missing template fails normally
- **WHEN** no configured template source provides a requested logical template
  path
- **THEN** rendering fails with the standard template-not-found behaviour for
  the renderer

### Requirement: Logical static asset namespace
The system SHALL serve static assets from a single logical namespace backed by
ordered configured module package static sources.

#### Scenario: Web core provides fallback static assets
- **WHEN** `web_core` is included as the earliest configured module
- **THEN** it contributes reusable baseline static assets as low-precedence
  defaults

#### Scenario: Omitted web core does not provide fallback static assets
- **WHEN** `web_core` is not included in the configured module list and no
  explicit filesystem static root is configured
- **THEN** runtime static serving and web validation do not read `web_core`
  baseline static assets

#### Scenario: Empty static mount preserves URL generation
- **WHEN** no configured module contributes static assets and no explicit
  filesystem static root is configured
- **THEN** the application still provides the configured static route name for
  URL generation, while requests for assets return a normal missing-asset
  response

#### Scenario: Later module static asset overrides earlier module asset
- **WHEN** multiple configured modules provide the same logical static asset path
- **THEN** the static asset resolver serves the first matching module asset
  according to reverse configured module order

#### Scenario: Module static assets use deterministic precedence
- **WHEN** configured modules provide package static asset sources
- **THEN** the resolver serves the first matching module asset according to
  reverse configured module order

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
- **THEN** it enumerates configured module package static sources using the same
  precedence as runtime static serving

#### Scenario: Static export writes winning assets
- **WHEN** multiple static sources provide the same logical static path
- **THEN** static export writes only the winning asset for that logical path to
  the export directory

#### Scenario: Static export avoids web startup
- **WHEN** static export loads composition and static sources
- **THEN** it does not import application FastAPI startup code, route modules,
  the Jinja environment, or identity-specific runtime state

#### Scenario: Static export belongs to web core
- **WHEN** static export is implemented
- **THEN** it is exposed by `web_core` rather than by `auth_ext`

#### Scenario: Static export reports duplicate defaults
- **WHEN** configured module package static sources provide duplicate logical
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
providers are registered by configured modules and resolved once at application
startup.

#### Scenario: Module registers context providers
- **WHEN** a configured module exposes a conventional `<module>.context` surface
- **THEN** the application calls its context registration hook with
  `add_to_context` so the module can register static dictionaries or
  request-time context providers

#### Scenario: Provider is resolved before requests
- **WHEN** the application starts
- **THEN** registered context providers are validated and invalid providers fail
  startup or validation

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

#### Scenario: Web core contributes reusable theme context
- **WHEN** `web_core` is included in the configured module list
- **THEN** it can contribute reusable theme context and theme update route
  information without requiring application-owned theme helpers

### Requirement: Application composition validation
The system SHALL validate configured module composition before runtime failures
are left to ordinary requests.

#### Scenario: Validation checks configured modules
- **WHEN** the validation command runs
- **THEN** it inspects configured modules, optional module surfaces, route
  exports, model metadata, package template sources, package static sources,
  and context provider registrations

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
- **WHEN** configured modules define conflicting route names or method/path pairs
- **THEN** validation reports the conflict before the application relies on
  route-order side effects
