## MODIFIED Requirements

### Requirement: ASGI application shell
The system SHALL provide a FastAPI/Starlette ASGI application shell with an
application factory and stable ASGI app import path.

#### Scenario: Application import requires resolved configuration
- **WHEN** a developer imports the documented ASGI app path for normal default
  startup
- **THEN** the import resolves application configuration through `APP_CONFIG` or
  the host project's `app.toml`
- **AND** missing application configuration fails with an actionable
  configuration error instead of starting with built-in defaults
- **AND** importing the app does not require database schema state

#### Scenario: Application can be constructed for tests
- **WHEN** tests call the application factory with explicit settings
- **THEN** a fresh FastAPI application instance is returned with those settings
  and baseline routes registered

## ADDED Requirements

### Requirement: Project command configuration boundary
The system SHALL make package-owned Wevra project commands resolve the concrete
host application project and application config before constructing normal
runtime settings.

#### Scenario: Command invoked from app project
- **WHEN** an operator runs a package-owned Wevra project command from the host
  application project directory
- **THEN** the command resolves that project and its `app.toml` as the
  application config boundary

#### Scenario: Command invoked from workspace root
- **WHEN** an operator runs a package-owned Wevra project command from a
  workspace root that unambiguously contains one configured Wevra host
  application project
- **THEN** the command resolves that host application project and its `app.toml`
  as the application config boundary

#### Scenario: Command cannot resolve app config
- **WHEN** a package-owned Wevra project command cannot resolve an application
  config file through `APP_CONFIG` or project discovery
- **THEN** the command fails with an actionable configuration error
- **AND** it does not continue with baked-in default settings

#### Scenario: Host app remains separate from reusable package
- **WHEN** Wevra project commands resolve the host application config
- **THEN** they use reusable project metadata and config-loading contracts
  rather than importing `uniquode.io` application modules directly

#### Scenario: Application config uses namespaced app tables
- **WHEN** a host application defines app-wide modules, routes, templates,
  static settings, or database configuration
- **THEN** those values live under `[app]`, `[app.routes]`, `[app.templates]`,
  and `[app.static]` rather than as global config tables

#### Scenario: Route module aliases are normalised
- **WHEN** `[app.routes]` contains a module key with hyphens such as
  `wevra-auth`
- **THEN** the route prefix mapping is applied to the dotted Python module name
  `wevra.auth`
- **AND** route labels inside that module mapping are not normalised

#### Scenario: Route module alias collisions are rejected
- **WHEN** `[app.routes]` contains multiple keys that normalise to the same
  Python module name
- **THEN** application config loading fails with a configuration error
