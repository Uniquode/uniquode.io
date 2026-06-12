## ADDED Requirements

### Requirement: Site startup entry point
Wevra SHALL provide a public startup entry point that composes configured Wevra modules into an existing FastAPI application instance and returns a `Site` object.

#### Scenario: Startup composes existing app
- **WHEN** a host application calls Wevra startup with an existing FastAPI app and an explicit config source
- **THEN** Wevra composes configured modules into that app
- **AND** startup returns a `Site` object representing the configured site

#### Scenario: Host app owns FastAPI construction
- **WHEN** a host application constructs `FastAPI()` before Wevra startup
- **THEN** Wevra startup uses that app instance instead of constructing a replacement app
- **AND** host-owned FastAPI metadata, middleware, exception handlers, lifespan, docs URLs, and instrumentation remain app-owned concerns

#### Scenario: Missing config source fails clearly
- **WHEN** Wevra startup cannot load the supplied config source
- **THEN** startup fails with an actionable configuration error
- **AND** it does not continue by applying hidden built-in app defaults

### Requirement: Site exposes public module capabilities
The `Site` object SHALL expose configured module capabilities and helpers through explicit public APIs rather than requiring host apps to construct Wevra internals.

#### Scenario: App asks for module capability
- **WHEN** a host app needs a Wevra-owned helper such as an auth dependency or route helper
- **THEN** it obtains that helper through the `Site` API or a module-owned capability returned by `Site`
- **AND** it does not instantiate the module's internal runtime objects directly

#### Scenario: Missing capability is explicit
- **WHEN** a host app requests a capability that is not configured or not provided
- **THEN** the `Site` API fails with an explicit error
- **AND** the failure identifies the missing owner or capability without exposing secret values

#### Scenario: Capability ownership is preserved
- **WHEN** a capability belongs to a configured Wevra module
- **THEN** the owning module defines the public capability surface
- **AND** host apps consume that surface without inspecting module-private settings or state

### Requirement: Wevra owns common initialisation
Wevra startup SHALL own common framework initialisation for configured modules, including route registration, database wiring, module settings construction, auth composition, and Wevra runtime helpers.

#### Scenario: Auth is composed by Wevra
- **WHEN** auth is configured for the site
- **THEN** Wevra startup initialises the auth runtime through Wevra-owned auth APIs
- **AND** the host app does not construct auth settings, auth delivery, FastAPI Users objects, or auth runtime state directly

#### Scenario: Database is composed by Wevra
- **WHEN** database configuration is available through the central config source
- **THEN** Wevra startup initialises database wiring through Wevra-owned database APIs
- **AND** the host app does not duplicate database URL handling or session-factory setup

#### Scenario: Routes are composed by configured modules
- **WHEN** modules are configured for the site
- **THEN** Wevra startup registers module routes using module-owned route declarations and configured route prefixes
- **AND** the host app does not hard-code Wevra route prefixes as fallback defaults

### Requirement: Host app remains product-focused
After Wevra startup, the host app SHALL only need to manage host-owned product routes, pages, templates, and behaviour.

#### Scenario: App adds product routes
- **WHEN** Wevra startup has completed
- **THEN** the host app can register its own user-facing routes and pages
- **AND** those routes may use public dependencies or helpers exposed through `Site`

#### Scenario: App avoids Wevra configuration manipulation
- **WHEN** host app code is inspected after migration
- **THEN** it does not manipulate Wevra-owned auth settings, database settings, route-prefix defaults, environment-backed Wevra settings, or module runtime state

#### Scenario: App uses public auth dependencies
- **WHEN** an app route needs login or superuser protection
- **THEN** it uses a public auth dependency or helper exposed by Wevra through `Site`
- **AND** it does not inspect auth internals to build that protection
