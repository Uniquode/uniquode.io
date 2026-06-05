## ADDED Requirements

### Requirement: Migration revision generation command
The system SHALL provide a project migration command for generating Alembic
revision files in configured module-owned migration locations.

#### Scenario: Revision command places file in owning module
- **WHEN** a developer runs `uv run migrate revision --module <module> -m <message>`
  for a configured importable module
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
- **WHEN** a developer views `uv run migrate revision --help`
- **THEN** the command help explains the usual roll-forward order of upgrading
  to the previous head, updating models, generating the owning module revision,
  reviewing generated operations and graph pointers, running upgrade, and
  running validation

#### Scenario: Existing migration commands remain unchanged
- **WHEN** a developer runs `uv run migrate upgrade`, `uv run migrate downgrade`,
  `uv run migrate current`, or `uv run migrate history`
- **THEN** those commands retain their existing arguments, database URL
  override behaviour, and Alembic operation mapping
