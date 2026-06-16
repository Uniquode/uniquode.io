# site-startup-api Specification

## Purpose
TBD - created by archiving change add-site-startup-api. Update Purpose after archive.
## Requirements
### Requirement: Site startup entry point
Wybra SHALL provide a public startup entry point that composes configured Wybra modules into an existing FastAPI application instance and returns a `Site` object.

#### Scenario: Startup composes existing app
- **WHEN** a host application calls Wybra startup with an existing FastAPI app and an explicit config source
- **THEN** Wybra composes configured modules into that app
- **AND** startup returns a `Site` object representing the configured site

#### Scenario: Host app owns FastAPI construction
- **WHEN** a host application constructs `FastAPI()` before Wybra startup
- **THEN** Wybra startup uses that app instance instead of constructing a replacement app
- **AND** host-owned FastAPI metadata, middleware, exception handlers, lifespan, docs URLs, and instrumentation remain app-owned concerns

#### Scenario: Missing config source fails clearly
- **WHEN** Wybra startup cannot load the supplied config source
- **THEN** startup fails with an actionable configuration error
- **AND** it does not continue by applying hidden built-in app defaults

### Requirement: Site exposes type-keyed capabilities
The `Site` object SHALL expose configured module capabilities and helpers through explicit type-keyed public APIs rather than requiring host apps to construct Wybra internals.

#### Scenario: App asks for module capability
- **WHEN** a host app or module needs a Wybra-owned helper such as an auth dependency, database session, or route helper
- **THEN** it obtains that helper by requiring the public capability type from `Site`
- **AND** it does not instantiate the provider module's internal runtime objects directly

#### Scenario: Missing capability is explicit
- **WHEN** a host app or module requires a capability type that is not provided
- **THEN** the `Site` API fails with an explicit error
- **AND** the failure identifies the missing capability type without exposing secret values

#### Scenario: Capability provider is replaceable
- **WHEN** a module provides an implementation for a public capability type
- **THEN** consumers request the capability by type rather than provider module name
- **AND** a different configured module can provide the same public capability type without changing consumers

#### Scenario: Duplicate capability provider fails
- **WHEN** more than one module attempts to provide the same capability type
- **THEN** startup fails with an explicit duplicate capability error
- **AND** Wybra does not silently choose one provider

### Requirement: Wybra owns common initialisation
Wybra startup SHALL own common framework initialisation for configured modules, including route registration, database wiring, module settings construction, auth composition, and Wybra runtime helpers.

#### Scenario: Auth is composed by Wybra
- **WHEN** auth is configured for the site
- **THEN** Wybra startup initialises the auth runtime through Wybra-owned auth APIs
- **AND** the host app does not construct auth settings, auth delivery, FastAPI Users objects, or auth runtime state directly

#### Scenario: Database is composed by Wybra
- **WHEN** database configuration is available through the central config source
- **THEN** Wybra startup initialises database wiring through Wybra-owned database APIs
- **AND** Wybra provides a public database capability with session and transaction context managers
- **AND** the host app does not duplicate database URL handling or session-factory setup

#### Scenario: Routes are composed by configured modules
- **WHEN** modules are configured for the site
- **THEN** Wybra startup discovers route surfaces from configured modules in module-list order
- **AND** registers only route surfaces explicitly published in route configuration
- **AND** uses configured route prefixes for published route surfaces
- **AND** the host app does not hard-code Wybra route prefixes as fallback defaults

#### Scenario: Route configuration is a publication allow-list
- **WHEN** a configured module exposes multiple route surfaces
- **AND** route configuration lists only some of those route surface labels
- **THEN** Wybra registers only the listed route surfaces
- **AND** leaves unlisted route surfaces unpublished

#### Scenario: Unknown published route surface fails clearly
- **WHEN** route configuration references a route surface label that the configured module does not expose
- **THEN** Wybra startup fails with an explicit route composition error
- **AND** the error identifies the configured module and unknown route surface label

#### Scenario: Earlier module routes override later module routes
- **WHEN** an earlier configured module and a later configured module expose the same normalised HTTP method and full route path
- **THEN** Wybra registers the earlier module's route
- **AND** skips the later duplicate route
- **AND** logs a structured warning identifying the winning module route and the skipped module route

#### Scenario: Module resources use first-module-wins precedence
- **WHEN** configured modules expose template or static resources with the same logical path
- **THEN** Wybra resolves the resource from the earliest configured module that provides it
- **AND** later resources remain shadowed without failing startup

### Requirement: Host app remains product-focused
After Wybra startup, the host app SHALL only need to manage host-owned product routes, pages, templates, and behaviour.

#### Scenario: App exposes product route surfaces
- **WHEN** the host app has product routes or pages
- **THEN** it exposes those routes through the configured module route surface
- **AND** Wybra discovers and registers those routes during startup according to module-list order
- **AND** app route handlers may use public dependencies or helpers exposed through `Site`

#### Scenario: App avoids Wybra configuration manipulation
- **WHEN** host app code is inspected after migration
- **THEN** it does not manipulate Wybra-owned auth settings, database settings, route-prefix defaults, environment-backed Wybra settings, or module runtime state

#### Scenario: App uses public auth dependencies
- **WHEN** an app route needs login or superuser protection
- **THEN** it uses a public auth capability required from `Site` by capability type
- **AND** it does not inspect auth internals to build that protection

### Requirement: Runserver supplies startup overrides

Wybra runserver SHALL expose CLI options for startup-level configuration overrides and pass those overrides into Wybra startup without requiring host app boilerplate.

#### Scenario: Runserver accepts startup override options

- **WHEN** a developer starts `wybra-runserver` with `--project`, `--config`, `--database-url`, or `--deploy`
- **THEN** runserver records those values as Wybra startup overrides
- **AND** forwards them into the ASGI app startup path

#### Scenario: Runserver keeps Uvicorn ownership separate

- **WHEN** a developer passes Uvicorn-specific arguments after the runserver options
- **THEN** runserver continues to pass those arguments to Uvicorn
- **AND** it does not treat Uvicorn arguments as Wybra startup config overrides

### Requirement: Startup reads effective environment channel

Wybra startup SHALL read the effective startup environment selected by runserver or the invoking process when no explicit in-process startup arguments have been supplied.

#### Scenario: ASGI startup receives runserver overrides

- **WHEN** `wybra-runserver` starts an app through Uvicorn
- **AND** startup overrides were supplied to runserver
- **THEN** runserver exposes those overrides through `APP_ROOT`, `APP_CONFIG`, `DATABASE_URL`, and `APP_ENV` for the server process
- **AND** the imported ASGI app startup path uses those values to select the project root, config file, database URL, and deployment environment before module setup

#### Scenario: Explicit in-process startup inputs win

- **WHEN** a test or embedded caller passes explicit startup inputs directly to `start()` or `start_site()`
- **THEN** Wybra uses those direct inputs
- **AND** it does not override them with values from the process environment channel unless that environment was explicitly supplied by the caller

### Requirement: Site exposes lazy capability proxies
The system SHALL expose a public site API for obtaining typed lazy capability proxies in addition to immediate capability lookup.

#### Scenario: Module requests capability proxy during setup
- **WHEN** module setup requests a lazy proxy for a capability type
- **THEN** the site returns a proxy without immediately requiring that capability to be registered

#### Scenario: Immediate capability lookup remains available
- **WHEN** startup genuinely requires a capability before continuing
- **THEN** the site can still perform immediate required lookup
- **AND** missing required startup capabilities fail during setup

### Requirement: Startup avoids eager runtime dependency binding
The system SHALL avoid resolving runtime-only cross-module capability dependencies during module setup.

#### Scenario: Runtime dependency is absent during setup
- **WHEN** a configured module depends on another capability only for runtime operations
- **THEN** module setup registers its own capability without requiring the runtime dependency to already exist

#### Scenario: Runtime dependency is missing at use time
- **WHEN** a runtime operation uses a lazy proxy for a capability that is absent
- **THEN** the operation fails with a clear capability error at the operation boundary
