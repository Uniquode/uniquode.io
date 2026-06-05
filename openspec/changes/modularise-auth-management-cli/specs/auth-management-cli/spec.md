## ADDED Requirements

### Requirement: Auth management package entry point
The system SHALL expose the `identitymgr` CLI through a package-owned entry
point that remains stable while the implementation is split into focused
modules.

#### Scenario: Project script remains stable
- **WHEN** a developer inspects project scripts after the refactor
- **THEN** `identitymgr` resolves to `auth_ext.identitymgr:main`

#### Scenario: Package exports main
- **WHEN** code imports `auth_ext.identitymgr`
- **THEN** the package exposes a callable `main` entry point equivalent to the
  current CLI entry point

#### Scenario: Existing imports continue to resolve
- **WHEN** tests or project code import `auth_ext.identitymgr` for CLI helpers
- **THEN** existing public helper imports used by the test suite continue to
  resolve or are updated through explicit package exports without changing CLI
  behaviour

### Requirement: Auth management command registration
The system SHALL compose the `identitymgr` Click command tree through explicit
registration functions rather than automatic plugin discovery.

#### Scenario: Root command registers resource components
- **WHEN** the root `identitymgr` Click command is constructed
- **THEN** user, group, and scope command components are registered explicitly
  with the root command tree

#### Scenario: Registration preserves command behaviour
- **WHEN** an operator runs existing `identitymgr` user, group, or scope
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
- **WHEN** a developer inspects the `auth_ext.identitymgr` package
- **THEN** user, group, and scope command registration live in separate modules
  or subpackages from the root CLI construction

#### Scenario: Shared helpers are separated by responsibility
- **WHEN** shared CLI helpers are moved out of the root command module
- **THEN** argument objects, schema checks, output formatting, password-source
  handling, timestamp parsing, and dispatcher helpers are grouped by
  responsibility rather than by resource command accident

#### Scenario: No new runtime dependencies
- **WHEN** the refactor is implemented
- **THEN** the project does not add runtime dependencies for command discovery,
  dependency injection, or plugin management

#### Scenario: Host application boundary is preserved
- **WHEN** the package split is complete
- **THEN** `auth_ext.identitymgr` modules continue to avoid imports from
  `uniquode` application code
