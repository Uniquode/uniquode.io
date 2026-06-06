## MODIFIED Requirements

### Requirement: Source package layout
The system SHALL use a workspace layout with `app/src/app` as the concrete
application package, while consuming reusable framework infrastructure from an
explicit `wevra` workspace dependency.

#### Scenario: Package imports from source layout
- **WHEN** the project is installed or run through `uv`
- **THEN** the `app` package resolves from `app/src/app`

#### Scenario: Infrastructure modules are external dependency
- **WHEN** a developer inspects the `app` source tree
- **THEN** reusable web infrastructure, data infrastructure, tooling, auth,
  model, migration, template, and static-resource framework code is not
  vendored under `app/src/app`, `app/src/web_ext`, or `app/src/wevra` in the
  application project

#### Scenario: Wevra is a workspace member during local development
- **WHEN** a developer runs the application in the local development workspace
- **THEN** the `wevra` package is provided by an adjacent workspace member
  dependency rather than by application-local source

#### Scenario: Application package excludes framework source
- **WHEN** the `app` project build metadata is inspected
- **THEN** it builds the `app` application package and does not include
  the `wevra` framework package as an application build module

#### Scenario: Web resources are module-owned
- **WHEN** a developer inspects the source tree or workspace dependencies
- **THEN** templates and static assets live in configured module package roots
  such as `src/<module>/templates/` and `src/<module>/static/`

#### Scenario: Feature modules may live beside the core package
- **WHEN** a later capability introduces an application feature module
- **THEN** the module may live alongside `app/src/app` in the application
  project and integrate through the configured module boundaries

### Requirement: Project metadata and toolchain
The system SHALL define Python project metadata in `pyproject.toml` for a
Python 3.13+ application managed by `uv` and built with `uv_build`.

#### Scenario: Project metadata exists
- **WHEN** a developer inspects the project root
- **THEN** `pyproject.toml` defines the project name, Python 3.13+ requirement,
  `uv_build` build backend, runtime dependencies, and development dependency
  groups

#### Scenario: Workspace framework dependency is declared
- **WHEN** a developer inspects `app` dependency metadata
- **THEN** `wevra` is listed as a project dependency
- **AND** the local workspace root may resolve `wevra` from a temporary ignored
  checkout while the framework is not yet available as a regular dependency

#### Scenario: Shared lock controls local dependency resolution
- **WHEN** a developer runs `uv` in the local workspace while `wevra/` is a
  workspace member
- **THEN** `uv` discovers the parent workspace
- **AND** the application and local Wevra dependency source resolve dependency
  versions from the parent `uv.lock`
- **AND** member-local lock files are not used for coordinated workspace
  development

#### Scenario: Tool configuration is discoverable
- **WHEN** a developer inspects `pyproject.toml`
- **THEN** configuration for Ruff, `ty`, and pytest is present or the file
  documents the command conventions needed to run them

### Requirement: Baseline validation commands
The system SHALL provide repeatable baseline validation commands for formatting,
linting, type checking, and tests.

#### Scenario: Application validation runs against workspace framework
- **WHEN** a developer runs the application validation suite from the `app`
  member directory
- **THEN** it imports `wevra` from the adjacent workspace member dependency and
  verifies application integration with that framework dependency

#### Scenario: Framework tests are not duplicated in application
- **WHEN** framework-specific web, data, auth, tooling, or namespace tests are
  inspected
- **THEN** they live in the `wevra` project rather than in the `app`
  application test suite

#### Scenario: Application repository does not validate framework internals
- **WHEN** repository CI or pre-commit validation runs for `uniquode`
- **THEN** it validates application formatting, linting, type checking, and
  tests
- **AND** it does not run Wevra-owned tests, linting, type checks, or
  package-build checks

#### Scenario: Pre-commit runs application validation
- **WHEN** pre-commit hooks run in the `uniquode` repository
- **THEN** they include the application `validate` command as a configuration
  and composition backstop
- **AND** that hook runs with `app` as the host project directory

#### Scenario: Application tests retain integration coverage
- **WHEN** the `app` test suite is inspected
- **THEN** it retains focused tests for application settings, startup,
  configured module loading, app routes, app templates, and project command
  adapters that depend on `wevra`

#### Scenario: OpenSpec remains application-owned
- **WHEN** the `wevra` project is extracted into its own repository
- **THEN** OpenSpec artifacts remain in the `uniquode` repository
- **AND** the `wevra` repository does not initialise or copy a separate
  OpenSpec change stream
