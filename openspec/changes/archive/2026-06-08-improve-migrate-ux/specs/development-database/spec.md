## MODIFIED Requirements

### Requirement: Development migrations are available
The system SHALL provide a clear mechanism for initialising and updating the
local SQLite development database schema through Alembic migrations.

#### Scenario: Local SQLite migration state can be initialised
- **WHEN** the project-root development database file does not yet contain
  Alembic migration state
- **THEN** `uv run wevra-migrate init` can create the SQLite database file and
  Alembic migration state without applying application schema revisions

#### Scenario: Local SQLite schema can be upgraded after init
- **WHEN** the project-root development database has Alembic migration state
  initialised at base
- **THEN** `uv run wevra-migrate upgrade` can apply Alembic migrations to
  create the required schema tables

#### Scenario: Upgrade requires migration state
- **WHEN** a developer runs `uv run wevra-migrate upgrade` against a database
  without Alembic migration state
- **THEN** the command fails with guidance to run `uv run wevra-migrate init`
  for first-time schema initialisation

#### Scenario: Migration command resolves effective configuration
- **WHEN** a developer runs the migration command without a database override
- **THEN** it applies migrations using the same effective database URL
  resolution as application settings

#### Scenario: Migration command accepts an explicit database override
- **WHEN** a developer runs the migration command with a database URL override
- **THEN** that URL is used for the migration command instead of the configured
  default

#### Scenario: Migration mechanism is explicit
- **WHEN** database lifecycle commands are run through `wevra-migrate init` and
  `wevra-migrate upgrade`
- **THEN** provisioning, migration-state initialisation, and schema upgrade
  behaviour are visible in command output or command failure guidance rather
  than being undocumented side effects

### Requirement: PostgreSQL provisioning is explicit
The system SHALL provision PostgreSQL database, user, role, and privilege setup
through explicit migration initialisation while keeping that work outside
application startup and ordinary migration upgrade.

#### Scenario: Init provisions PostgreSQL
- **WHEN** `uv run wevra-migrate init` runs against PostgreSQL with an
  administrative database URL available
- **THEN** it provisions the target database, user, role, and privileges before
  initialising Alembic migration state at base through the application
  connection

#### Scenario: Application does not create PostgreSQL databases or roles
- **WHEN** the application connects to a PostgreSQL database
- **THEN** it does not attempt to create databases, users, roles, or privileges
  as part of ordinary startup

#### Scenario: Migration upgrade does not provision PostgreSQL
- **WHEN** `uv run wevra-migrate upgrade` cannot connect to PostgreSQL because
  the database, user, role, or privilege boundary is missing
- **THEN** the command fails with a safe connection or provisioning diagnostic
  instead of attempting privileged provisioning through the application
  connection

#### Scenario: Missing PostgreSQL admin connection is reported safely
- **WHEN** `uv run wevra-migrate init` runs against PostgreSQL and cannot
  provision with an administrative database URL
- **THEN** the command fails with a safe diagnostic that names the missing
  admin connection requirement without leaking credentials or raw driver traces

### Requirement: Migration command Click parser
The system SHALL use Click for the `wevra-migrate` command parser while
preserving database URL override behaviour and exposing explicit lifecycle
commands for initialisation, upgrade, status inspection, history, downgrade,
and revision generation.

#### Scenario: Migration subcommands remain available
- **WHEN** a developer runs `uv run wevra-migrate init`,
  `uv run wevra-migrate upgrade`, `uv run wevra-migrate downgrade`,
  `uv run wevra-migrate current`, or `uv run wevra-migrate history`
- **THEN** the command invokes the matching lifecycle or Alembic operation with
  the documented revision argument requirements

#### Scenario: Database URL override remains available
- **WHEN** a developer runs `uv run wevra-migrate --database-url <url> upgrade`
- **THEN** the supplied database URL is used for that migration command instead
  of the configured default

#### Scenario: Subcommand-level database URL override remains available
- **WHEN** a developer runs
  `uv run wevra-migrate upgrade --database-url <url>`
- **THEN** the supplied database URL is used for that migration command instead
  of the configured default

#### Scenario: Init accepts PostgreSQL admin URL override
- **WHEN** a developer runs
  `uv run wevra-migrate init --admin-database-url <url>`
- **THEN** the supplied admin URL is used for PostgreSQL provisioning while the
  configured or overridden application database URL remains the migration
  target

#### Scenario: Current reports uninitialised database
- **WHEN** a developer runs `uv run wevra-migrate current` against a reachable
  database without Alembic migration state
- **THEN** the command reports that the database is not initialised and exits
  successfully because status inspection completed

#### Scenario: Current reports connection failure safely
- **WHEN** a developer runs `uv run wevra-migrate current` against an
  unavailable configured database
- **THEN** the command fails with a safe diagnostic that does not leak database
  credentials or raw driver traces

#### Scenario: Revision command remains configured consistently
- **WHEN** a developer runs `uv run wevra-migrate revision`
- **THEN** the command uses the same effective database URL, app configuration,
  model metadata, and composed module migration locations as the other
  migration commands
