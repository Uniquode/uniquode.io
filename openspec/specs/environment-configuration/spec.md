# environment-configuration Specification

## Purpose
Define how application runtime configuration, local dotenv workflows, database
URLs, and secret-safe validation are provided through envex-backed settings.

## Requirements

### Requirement: Environment-backed settings
The system SHALL load application runtime configuration from environment
variables through the `envex` module.

#### Scenario: Default settings use environment values
- **WHEN** the application is created without explicit settings
- **THEN** it uses envex-backed environment configuration for supported runtime
  settings

#### Scenario: Environment names remain concise
- **WHEN** supported application environment variables are documented or
  validated
- **THEN** conventional names such as `DATABASE_URL` are used directly and
  app-specific names use concise names such as `APP_ENV`, `APP_RELOAD`, and
  `CSRF_SECRET`

#### Scenario: Explicit settings remain available
- **WHEN** tests or callers construct `Settings` with explicit values
- **THEN** those values can be used without mutating process environment

#### Scenario: Settings loading mechanics are reusable
- **WHEN** an application uses the shared envex and app composition pattern
- **THEN** reusable typed environment parsing, app configuration loading, and
  settings factory invocation are provided by `wevra.core`, while concrete
  settings fields and deployment policy remain application-owned

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
