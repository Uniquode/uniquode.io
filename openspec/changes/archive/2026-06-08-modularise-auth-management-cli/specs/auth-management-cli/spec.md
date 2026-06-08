## ADDED Requirements

### Requirement: Auth management package entry point
The system SHALL expose the `wevra-authmgr` CLI through the package-owned
`wevra.auth.cli.authmgr:main` entry point while the implementation is split into
focused modules.

#### Scenario: Project script uses authmgr package
- **WHEN** a developer inspects project scripts after the refactor
- **THEN** `wevra-authmgr` resolves to `wevra.auth.cli.authmgr:main`

#### Scenario: Package exports main
- **WHEN** code imports `wevra.auth.cli.authmgr`
- **THEN** the package exposes a callable `main` entry point equivalent to the
  current CLI entry point

#### Scenario: Package exports public surface
- **WHEN** code imports `wevra.auth.cli.authmgr`
- **THEN** the package exposes the supported public CLI surface for root command
  construction, argument typing, password-source typing, program naming, and
  `main`
- **AND** internal helpers are imported from their defining modules instead of
  being re-exported from the package root

### Requirement: Auth management command registration
The system SHALL compose the `wevra-authmgr` Click command tree through explicit
registration functions rather than automatic plugin discovery.

#### Scenario: Root command registers resource components
- **WHEN** the root auth-management Click command is constructed
- **THEN** user, group, and scope command components are registered explicitly
  with the root command tree

#### Scenario: Registration preserves command behaviour
- **WHEN** an operator runs existing `wevra-authmgr` user, group, or scope
  commands
- **THEN** command names, options, arguments, help output, output formats,
  validation behaviour, and exit statuses remain unchanged from the pre-refactor
  command behaviour

#### Scenario: Registration failure is explicit
- **WHEN** a command component cannot be imported or registered during CLI
  construction
- **THEN** the failure is surfaced as a normal import or construction failure
  rather than being silently ignored

#### Scenario: Automatic discovery is not used
- **WHEN** the CLI starts
- **THEN** it does not scan packages, entry points, filesystem paths, or dynamic
  plugin registries to discover command modules

### Requirement: Auth management module boundaries
The system SHALL split auth-management CLI responsibilities into focused
modules without adding new runtime dependencies.

#### Scenario: Resource commands are separated
- **WHEN** a developer inspects the `wevra.auth.cli.authmgr` package
- **THEN** user, group, and scope command registration live in separate modules
  or subpackages from the root CLI construction

#### Scenario: Shared helpers are separated by responsibility
- **WHEN** shared CLI helpers are moved out of the root command module
- **THEN** argument objects, schema checks, output formatting, password-source
  handling, timestamp parsing, and dispatcher helpers are grouped by
  responsibility rather than by resource command accident

#### Scenario: Cross-command helpers are shared outside auth modules
- **WHEN** a CLI helper handles project configuration, database URL resolution,
  database/session setup, schema preflight wiring, or common operator
  diagnostics needed by another Wevra command
- **THEN** that helper lives in a shared Wevra CLI/tooling module rather than
  under `wevra.auth.cli.authmgr`
- **AND** `wevra-authmgr` uses the shared helper instead of duplicating
  command-private logic

#### Scenario: No new runtime dependencies
- **WHEN** the refactor is implemented
- **THEN** the project does not add runtime dependencies for command discovery,
  dependency injection, or plugin management

#### Scenario: Host application boundary is preserved
- **WHEN** the package split is complete
- **THEN** `wevra.auth.cli.authmgr` modules continue to avoid imports from
  `uniquode` application code

## MODIFIED Requirements

### Requirement: User group membership options
The `wevra-authmgr` command SHALL support group membership while creating or
updating users.

#### Scenario: Create user with groups
- **WHEN** an operator runs `wevra-authmgr user create <email>
  --group <id-or-abbrev>` one or more times
- **THEN** the command creates the user and assigns the user to the supplied
  groups

#### Scenario: Add group to user
- **WHEN** an operator runs `wevra-authmgr user update <user-target>
  --add-group <id-or-abbrev>`
- **THEN** the command adds the user to that group without replacing other group
  memberships

#### Scenario: Remove group from user
- **WHEN** an operator runs `wevra-authmgr user update <user-target>
  --rm-group <id-or-abbrev>`
- **THEN** the command removes the user from that group without changing other
  group memberships

#### Scenario: Set user groups
- **WHEN** an operator runs `wevra-authmgr user update <user-target>
  --set-group <id-or-abbrev>` one or more times
- **THEN** the command replaces the user's direct group memberships with exactly
  the supplied groups

#### Scenario: Group replacement is explicit
- **WHEN** an operator runs `wevra-authmgr user update <user-target>
  --group <id-or-abbrev>`
- **THEN** the command rejects the option because replacement uses `--set-group`
  and incremental updates use `--add-group` or `--rm-group`

#### Scenario: Group replacement excludes incremental changes
- **WHEN** an operator runs `wevra-authmgr user update <user-target>` with
  `--set-group` and either `--add-group` or `--rm-group`
- **THEN** the command rejects the invocation instead of layering replacement
  and incremental edits
