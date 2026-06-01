## ADDED Requirements

### Requirement: Migration command Click parser
The system SHALL use Click for the `migrate` command parser while preserving
the existing Alembic migration command interface and database URL override
behaviour.

#### Scenario: Migration subcommands remain available
- **WHEN** a developer runs `uv run migrate upgrade`, `uv run migrate downgrade`,
  `uv run migrate current`, or `uv run migrate history`
- **THEN** the command invokes the matching Alembic operation with the same
  revision argument requirements as before the parser migration

#### Scenario: Database URL override remains available
- **WHEN** a developer runs `uv run migrate --database-url <url> upgrade`
- **THEN** the supplied database URL is used for that migration command instead
  of the configured default

#### Scenario: Subcommand-level database URL override remains available
- **WHEN** a developer runs `uv run migrate upgrade --database-url <url>`
- **THEN** the supplied database URL is used for that migration command instead
  of the configured default
