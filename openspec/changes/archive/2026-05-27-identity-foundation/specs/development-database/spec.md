## ADDED Requirements

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
The system SHALL provide a clear mechanism for initialising the local SQLite development database schema through Alembic migrations.

#### Scenario: Local SQLite schema can be initialised
- **WHEN** the project-root development database file does not yet contain the current schema
- **THEN** a development setup path or startup policy can apply Alembic migrations to create the required tables

#### Scenario: Migration mechanism is explicit
- **WHEN** migrations are applied automatically or through a command
- **THEN** the behaviour is visible in configuration, validation, or command output rather than being an undocumented side effect

### Requirement: PostgreSQL provisioning remains external
The system SHALL treat PostgreSQL database, user, role, and privilege setup as environment provisioning outside application startup.

#### Scenario: PostgreSQL database is pre-provisioned
- **WHEN** the application runs against PostgreSQL in staging or production
- **THEN** it expects the database, user, and required privileges to already exist before application startup

#### Scenario: Application does not create PostgreSQL databases or roles
- **WHEN** the application connects to a PostgreSQL database
- **THEN** it does not attempt to create databases, users, roles, or privileges as part of ordinary startup
