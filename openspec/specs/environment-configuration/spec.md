# environment-configuration Specification

## Purpose
Define how application runtime configuration, local dotenv workflows, database
URLs, and secret-safe validation are provided through envex-backed settings.
## Requirements
### Requirement: Environment-backed settings
The system SHALL load application runtime configuration from environment variables through the `envex` module and expose those raw values through the central configuration provider before owner-specific typed settings are built.

#### Scenario: Default settings use environment values
- **WHEN** the application is created without explicit settings
- **THEN** it uses envex-backed environment configuration for supported runtime settings

#### Scenario: Environment names remain concise
- **WHEN** supported application environment variables are documented or validated
- **THEN** conventional names such as `DATABASE_URL` are used directly and app-specific names use concise names such as `APP_ENV`, `APP_RELOAD`, and `CSRF_SECRET`

#### Scenario: Explicit settings remain available
- **WHEN** tests or callers construct host app settings with explicit values
- **THEN** those host-owned values can be used without mutating process environment or constructing dependency-owned settings objects

#### Scenario: Settings loading mechanics are reusable
- **WHEN** an application uses the shared envex and app composition pattern
- **THEN** reusable environment parsing, app configuration loading, central config construction, and settings-provider access are provided by `wevra.core` or `wevra.config`, while concrete typed settings fields and deployment policy remain owned by the module that uses them

#### Scenario: Module settings are not app settings
- **WHEN** a reusable module defines typed settings for its own behaviour
- **THEN** those settings are loaded through the module's settings interface rather than being added to the host app settings object

### Requirement: `.env` support
The system SHALL support envex `.env` loading for local development
configuration.

#### Scenario: Local dotenv configuration is loaded
- **WHEN** a developer provides a supported `.env` file
- **THEN** envex can load configured application settings from that file

#### Scenario: Encrypted dotenv workflows are supported
- **WHEN** a developer uses envex encrypted/decrypted `.env` functionality
- **THEN** the application configuration path remains compatible with that
  workflow rather than requiring custom dotenv parsing

### Requirement: Database URL configuration
The system SHALL support database configuration through envex `DATABASE_URL`
handling.

#### Scenario: PostgreSQL credentials are injected
- **WHEN** a deployment environment supplies a PostgreSQL `DATABASE_URL`
- **THEN** the application uses that URL to connect without credentials being
  committed to the repository

#### Scenario: Local defaults remain available
- **WHEN** no database URL is supplied by the environment
- **THEN** the application falls back to the accepted local development database
  default

### Requirement: Explicit database lifecycle tooling
The system SHALL keep PostgreSQL database lifecycle operations separate from web
application startup.

#### Scenario: Database lifecycle utility is available
- **WHEN** explicit PostgreSQL database creation or destruction tooling is
  implemented
- **THEN** it can use `dbscripts` from
  `https://github.com/deeprave/dbscripts`

#### Scenario: Application startup does not provision PostgreSQL
- **WHEN** the web application starts against a PostgreSQL database URL
- **THEN** it does not create or destroy PostgreSQL databases as an implicit
  startup side effect

### Requirement: Secret-safe validation output
The system SHALL validate environment-backed settings without exposing secret
values.

#### Scenario: Verbose validation masks database credentials
- **WHEN** `validate --verbose` reports the effective database configuration
- **THEN** it does not print secret-bearing credentials from the database URL

#### Scenario: Verbose validation masks database query secrets
- **WHEN** `validate --verbose` reports a database URL with sensitive query
  parameters such as passwords, tokens, keys, or secrets
- **THEN** it redacts those query parameter values before printing the URL

#### Scenario: Validation reports missing or unsupported configuration
- **WHEN** required environment-backed settings are missing or unsupported
- **THEN** `validate` reports actionable diagnostics without printing secret
  values

### Requirement: Application config boundary

The system SHALL require a resolved application config file for normal environment/project configuration loading used by default app startup and package-owned project commands.

#### Scenario: APP_CONFIG selects app configuration

- **WHEN** `APP_CONFIG` names an application config file
- **THEN** normal project command and default app startup configuration loading uses that file as the application config boundary
- **AND** relative `APP_CONFIG` values are resolved from the effective project root
- **AND** `APP_CONFIG` does not change the effective project root

#### Scenario: Project app config is discovered

- **WHEN** no `APP_CONFIG` is set and a Wevra host project with `app.toml` can be resolved
- **THEN** normal project command and default app startup configuration loading uses that `app.toml` as the application config boundary
- **AND** the effective project root is the runtime project root used to locate that default config file

#### Scenario: Explicit project root wins

- **WHEN** startup supplies an explicit project root through `--project` or `APP_ROOT`
- **THEN** normal project command and default app startup configuration loading uses that project root for relative path resolution
- **AND** the config file path does not replace the explicit project root

#### Scenario: Missing app config fails fast

- **WHEN** no `APP_CONFIG` or project `app.toml` can be resolved for normal project command or default app startup configuration loading
- **THEN** configuration loading fails with an actionable error instead of constructing application settings from built-in defaults

#### Scenario: Explicit settings construction remains available

- **WHEN** tests or specialised callers construct settings explicitly without using environment/project config loading
- **THEN** those explicit settings remain usable without requiring an application config file

### Requirement: Application database environment precedence

The system SHALL resolve application database URL values in a deterministic order when loading settings from application config.

#### Scenario: CLI database override wins

- **WHEN** startup supplies an explicit database URL override
- **THEN** the application database URL comes from that startup override
- **AND** database, auth, validation, and migration consumers observe the same effective value

#### Scenario: Shared database override wins

- **WHEN** `DATABASE_URL` is set during application or auth settings loading
- **AND** no startup database URL override was supplied
- **THEN** the application database URL comes from `DATABASE_URL`

#### Scenario: Auth-specific database override is not supported

- **WHEN** `AUTH_DATABASE_URL` is set and `DATABASE_URL` is not set during auth settings loading
- **THEN** the application database URL does not come from `AUTH_DATABASE_URL`

#### Scenario: Application database config is default

- **WHEN** no startup database override or `DATABASE_URL` is set during application or auth settings loading
- **THEN** the application database URL comes from `database_url` in the resolved `[app]` config table

#### Scenario: Relative database paths use effective project root

- **WHEN** the effective application database URL contains a relative SQLite file path
- **THEN** the path is resolved relative to the effective project root
- **AND** it is not resolved relative to the Wevra package root or an accidental process current directory

### Requirement: Environment source adapter
The system SHALL provide one environment-backed source adapter that can feed
environment-derived values into the central configuration service using
registered config definition metadata.

#### Scenario: Environment source is constructed explicitly
- **WHEN** app startup or a CLI command has selected an environment mapping
- **THEN** it can construct an environment source from that mapping and inject
  it into the configuration service

#### Scenario: Environment source emits canonical values
- **WHEN** the environment source loads
- **THEN** it returns parsed configuration values using the same section and key
  structure used by configuration service mappings

#### Scenario: Definition defines environment override
- **WHEN** a registered config definition maps a field to one environment
  variable
- **THEN** the environment source applies that environment value as the raw
  value for the mapped field

#### Scenario: Definition defines environment fallback list
- **WHEN** a registered config definition maps a field to multiple environment
  variables
- **THEN** the environment source uses the first configured environment variable
  present in the selected environment mapping

#### Scenario: Existing settings construction remains available
- **WHEN** tests or specialised callers construct settings explicitly without
  using the configuration service
- **THEN** explicit settings construction remains available without requiring
  an environment source

### Requirement: File source adapter
The system SHALL provide a file-backed source adapter that reads a file selected
by app startup or CLI entrypoints.

#### Scenario: File source receives resolved filename
- **WHEN** app startup or a CLI command resolves the application config file
- **THEN** it passes that filename to the file source constructor before loading
  the configuration service

#### Scenario: File source reports parse diagnostics
- **WHEN** a file-backed source cannot parse or validate its input
- **THEN** it reports a secret-safe diagnostic with source metadata

#### Scenario: File source can include source location metadata
- **WHEN** a file-backed source can identify where a value or diagnostic came
  from
- **THEN** it can include file, line, or column metadata

### Requirement: Environment loading is Wevra-owned for generated and basic sites
A generated or basic Wevra site SHALL NOT require host-app environment loader code. Wevra SHALL provide the environment source loading, optional dotenv loading, and typed raw-value parsing needed by the configuration service and Wevra-owned commands.

#### Scenario: Host app has no environment loader module
- **WHEN** a basic Wevra site is generated or cleaned
- **THEN** no app-owned `environment.py` module is required for startup or Wevra CLI commands

#### Scenario: Dotenv support is centralised
- **WHEN** local dotenv loading is required
- **THEN** Wevra loads it through a Wevra-owned environment source
- **AND** host apps do not wrap dotenv loading themselves

#### Scenario: Env parsing remains minimal
- **WHEN** Wevra parses environment-backed values
- **THEN** it exposes only required behaviours such as lookup, presence checks, bool/int coercion, path handling, and secret-safe diagnostics
- **AND** additional environment framework complexity is not exposed to host apps

### Requirement: Envex is not an app-facing requirement
If `envex` remains in use, it SHALL be encapsulated inside Wevra-owned environment/configuration code and SHALL NOT be required as an app-facing integration layer.

#### Scenario: Envex remains internally useful
- **WHEN** Wevra uses `envex` for required dotenv or parsing behaviour
- **THEN** app code imports Wevra environment/config APIs rather than `envex` or app-owned wrappers around `envex`

#### Scenario: Envex behaviour is unnecessary
- **WHEN** Wevra only needs simple environment lookup and coercion that can be provided directly
- **THEN** the implementation may simplify or remove `envex` usage rather than preserving it by default

### Requirement: Deployment environment startup override

The system SHALL allow runserver startup to override the effective application deployment environment through the `--deploy` option.

#### Scenario: CLI deployment override wins

- **WHEN** startup supplies a deployment environment through `--deploy`
- **THEN** the effective application deployment environment comes from that startup override
- **AND** auth, CSRF, validation, and other deployment-policy consumers observe the same effective value

#### Scenario: Config deployment value is default

- **WHEN** no startup deployment override is supplied
- **THEN** the effective application deployment environment comes from configured application/environment sources

