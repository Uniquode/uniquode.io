## ADDED Requirements

### Requirement: Environment-backed settings
The system SHALL load application runtime configuration from environment
variables through the `envex` module.

#### Scenario: Default settings use environment values
- **WHEN** the application is created without explicit settings
- **THEN** it uses envex-backed environment configuration for supported runtime
  settings

#### Scenario: Explicit settings remain available
- **WHEN** tests or callers construct `Settings` with explicit values
- **THEN** those values can be used without mutating process environment

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

#### Scenario: Validation reports missing or unsupported configuration
- **WHEN** required environment-backed settings are missing or unsupported
- **THEN** `validate` reports actionable diagnostics without printing secret
  values
