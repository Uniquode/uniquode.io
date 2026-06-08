# development-database Specification

## Purpose
Define the local development database defaults, explicit ephemeral database
support, migration expectations, and PostgreSQL provisioning boundary.
## Requirements
### Requirement: Persistent local development database
The system SHALL default ordinary local development to a persistent SQLite database file at the project root.

#### Scenario: Default database is persistent for development
- **WHEN** a developer starts the application without overriding database configuration
- **THEN** the configured database URL points to a SQLite database file in the project root rather than to in-memory SQLite

#### Scenario: Local database file is not tracked
- **WHEN** the project-root SQLite database file is created
- **THEN** it is excluded from version control by the repository ignore rules

### Requirement: In-memory SQLite remains explicitly supported
The system SHALL continue supporting in-memory SQLite for tests and explicitly configured ephemeral runs.

#### Scenario: Tests can use in-memory SQLite
- **WHEN** tests need isolated database state
- **THEN** they can configure `sqlite+aiosqlite:///:memory:` explicitly without relying on the development default

#### Scenario: Ephemeral runs are opt-in
- **WHEN** a developer wants a disposable database
- **THEN** they can explicitly configure an in-memory SQLite database URL

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
- **THEN** it applies migrations using the same effective database URL resolution as application settings

#### Scenario: Migration command accepts an explicit database override
- **WHEN** a developer runs the migration command with a database URL override
- **THEN** that URL is used for the migration command instead of the configured default

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
  `uv run wevra-migrate upgrade`,
  `uv run wevra-migrate downgrade`, `uv run wevra-migrate current`, or
  `uv run wevra-migrate history`
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

### Requirement: Migration revision generation command
The system SHALL provide a project migration command for generating Alembic
revision files in configured module-owned migration locations.

#### Scenario: Revision command places file in owning module
- **WHEN** a developer runs
  `uv run wevra-migrate revision --module <module> -m <message>` for a
  configured importable module
- **THEN** the command invokes Alembic revision generation with `version_path`
  set to that module's conventional `<module>/migrations/versions/` location

#### Scenario: Revision command requires explicit module ownership
- **WHEN** a developer runs the revision command without an owning module
- **THEN** the command fails with usage output that explains the required
  module selection

#### Scenario: Unconfigured module is rejected
- **WHEN** a developer requests revision generation for an importable package
  that is not present in the active composition configuration
- **THEN** the command fails without creating a revision file for that package

#### Scenario: First module revision location is supported
- **WHEN** a configured importable module has no existing migration version
  directory
- **THEN** the command can create a revision in the module's conventional
  migration version location

#### Scenario: Autogenerate uses effective migration configuration
- **WHEN** a developer runs the revision command with `--autogenerate`
- **THEN** Alembic receives the same effective database URL, app
  configuration, model metadata, and composed version locations used by the
  migration upgrade command

#### Scenario: Revision graph options are preserved
- **WHEN** a developer supplies Alembic graph options such as `--head`,
  `--splice`, `--branch-label`, `--depends-on`, or `--rev-id`
- **THEN** the command passes those options to Alembic revision generation
  while still placing the generated file in the selected owning module

#### Scenario: Roll-forward order is visible in help
- **WHEN** a developer views `uv run wevra-migrate revision --help`
- **THEN** the command help explains the usual roll-forward order of upgrading
  to the previous head, updating models, generating the owning module revision,
  reviewing generated operations and graph pointers, running upgrade, and
  running validation

#### Scenario: Existing migration commands remain unchanged
- **WHEN** a developer runs `uv run wevra-migrate upgrade`,
  `uv run wevra-migrate downgrade`, `uv run wevra-migrate current`, or
  `uv run wevra-migrate history`
- **THEN** those commands retain their existing arguments, database URL
  override behaviour, and Alembic operation mapping
