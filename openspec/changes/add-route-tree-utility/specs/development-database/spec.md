## MODIFIED Requirements

### Requirement: Migration command Click parser
The system SHALL use Click for the `wevra-migrate` command parser while
preserving the existing Alembic migration subcommand interface and database URL
override behaviour.

#### Scenario: Migration subcommands remain available
- **WHEN** a developer runs `uv run wevra-migrate upgrade`,
  `uv run wevra-migrate downgrade`, `uv run wevra-migrate current`, or
  `uv run wevra-migrate history`
- **THEN** the command invokes the matching Alembic operation with the same
  revision argument requirements as before the command-prefix change

#### Scenario: Database URL override remains available
- **WHEN** a developer runs `uv run wevra-migrate --database-url <url> upgrade`
- **THEN** the supplied database URL is used for that migration command instead
  of the configured default

#### Scenario: Subcommand-level database URL override remains available
- **WHEN** a developer runs
  `uv run wevra-migrate upgrade --database-url <url>`
- **THEN** the supplied database URL is used for that migration command instead
  of the configured default
