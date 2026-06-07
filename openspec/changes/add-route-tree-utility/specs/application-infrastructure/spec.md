## MODIFIED Requirements

### Requirement: Project metadata and toolchain
The system SHALL define Python project metadata for a Python 3.13+ application
managed by `uv`, with the repository root acting as a local workspace
coordinator, `app` acting as the buildable application project, and Wevra
owning reusable operator command scripts.

#### Scenario: Workspace metadata exists
- **WHEN** a developer inspects the project root
- **THEN** `pyproject.toml` defines the workspace name, Python 3.13+
  requirement, workspace dependencies, development dependency groups, and
  `package = false`

#### Scenario: Application metadata exists
- **WHEN** a developer inspects `app/pyproject.toml`
- **THEN** it defines the `app` project name, Python 3.13+ requirement,
  `uv_build` build backend, runtime dependencies, development dependency
  groups, and application package build metadata
- **AND** it does not need to re-declare Wevra-owned operator scripts

#### Scenario: Wevra command scripts are package-owned and prefixed
- **WHEN** a developer inspects `wevra/pyproject.toml`
- **THEN** the package exposes `wevra-runserver`, `wevra-migrate`,
  `wevra-routes`, `wevra-validate`, and `wevra-identitymgr`
- **AND** it does not expose unprefixed operator command names that are likely
  to collide with host application or environment-specific commands

#### Scenario: Project is initialized through uv
- **WHEN** the initialization implementation creates `pyproject.toml`
- **THEN** it uses `uv` project initialization rather than writing
  `pyproject.toml` directly

#### Scenario: Git repository is initialized by project tooling
- **WHEN** project initialization completes
- **THEN** the repository has a Git repository initialized by `uv` project
  setup

#### Scenario: Tool configuration is discoverable
- **WHEN** a developer inspects `pyproject.toml`
- **THEN** configuration for Ruff, `ty`, and pytest is present or the file
  documents the command conventions needed to run them

#### Scenario: Workspace framework dependency is declared
- **WHEN** a developer inspects application dependency metadata
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

### Requirement: Baseline validation commands
The system SHALL provide repeatable baseline validation commands for
formatting, linting, type checking, and tests.

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
- **THEN** they include the `wevra-validate` command as a configuration and
  composition backstop
- **AND** that hook runs with `app` as the host project directory

#### Scenario: Application tests retain integration coverage
- **WHEN** the `app` test suite is inspected
- **THEN** it retains focused tests for application settings, startup,
  configured module loading, app routes, app templates, and Wevra command
  adapters used by the host project

#### Scenario: OpenSpec remains application-owned
- **WHEN** the `wevra` project is extracted into its own repository
- **THEN** OpenSpec artifacts remain in the `uniquode` repository
- **AND** the `wevra` repository does not initialise or copy a separate
  OpenSpec change stream

#### Scenario: Formatting check runs
- **WHEN** a developer runs the documented formatting command
- **THEN** Ruff formats or verifies the Python source and tests

#### Scenario: Lint check runs
- **WHEN** a developer runs the documented lint command
- **THEN** Ruff checks the Python source and tests

#### Scenario: Type check runs
- **WHEN** a developer runs the documented type-check command
- **THEN** `ty` checks the Python source package

#### Scenario: Test suite runs
- **WHEN** a developer runs the documented test command
- **THEN** pytest runs the available test suite

### Requirement: Local runtime command
The system SHALL provide a package-owned runtime command named
`wevra-runserver` for local execution of the configured host ASGI application
through `uv`.

#### Scenario: Prefixed package script is defined
- **WHEN** a developer inspects `wevra/pyproject.toml`
- **THEN** the project metadata defines a `wevra-runserver` command

#### Scenario: Host application supplies the stable ASGI app target
- **WHEN** a developer runs the documented local server command
- **THEN** Wevra resolves the host project metadata
- **AND** it starts Uvicorn against the configured host ASGI application target

#### Scenario: Runtime command implementation is tool-owned
- **WHEN** a developer inspects the `wevra-runserver` package script entry point
- **THEN** the command wrapper is provided by `wevra.tools`
  while still targeting the configured host application

#### Scenario: Runtime command is invoked through uv
- **WHEN** local development instructions reference the server startup command
- **THEN** they use `uv run wevra-runserver`

### Requirement: Local runtime defaults
The system SHALL define the baseline local runtime behaviour of the
`wevra-runserver` command for host, port, and reload operation.

#### Scenario: Local runtime uses development-oriented defaults
- **WHEN** a developer runs `uv run wevra-runserver` without additional
  arguments
- **THEN** the application starts with the documented local host, port, and
  reload defaults

#### Scenario: Local runtime accepts explicit overrides
- **WHEN** a developer runs `uv run wevra-runserver` with supported host, port,
  or reload command-line options
- **THEN** the application starts with the supplied values instead of the
  baseline defaults

#### Scenario: Reload falls back to environment configuration
- **WHEN** a developer runs `uv run wevra-runserver` without `--reload` and
  `APP_RELOAD` is set to a truthy value
- **THEN** the application starts with reload enabled

#### Scenario: Runtime contract stays independent of front-end tooling
- **WHEN** the local runtime command is reviewed
- **THEN** it does not require a front-end asset pipeline in order to start the
  ASGI application

### Requirement: Runtime command Uvicorn pass-through
The system SHALL allow the `wevra-runserver` command to forward additional
command-line arguments to Uvicorn after a `--` separator while preserving the
configured host ASGI target and local runtime defaults.

#### Scenario: Uvicorn arguments are forwarded
- **WHEN** a developer runs
  `uv run wevra-runserver -- --forwarded-allow-ips 127.0.0.1`
- **THEN** the command invokes Uvicorn for the configured host ASGI application
  with `--forwarded-allow-ips 127.0.0.1`

#### Scenario: Project runtime options still apply
- **WHEN** a developer runs
  `uv run wevra-runserver --host 0.0.0.0 --port 9000 -- --proxy-headers`
- **THEN** the command applies the project `--host` and `--port` options and
  passes `--proxy-headers` through to Uvicorn

#### Scenario: Application target remains project-owned
- **WHEN** a developer runs `uv run wevra-runserver -- other.asgi:app`
- **THEN** the command rejects the extra application target instead of passing
  two positional application targets to Uvicorn

#### Scenario: Reload environment fallback remains available
- **WHEN** a developer runs `uv run wevra-runserver -- <uvicorn args>` without
  the project `--reload` option and `APP_RELOAD` is set to a truthy value
- **THEN** the command starts Uvicorn with reload enabled and preserves the
  supplied Uvicorn arguments

#### Scenario: Reload environment fallback can be disabled explicitly
- **WHEN** a developer runs `uv run wevra-runserver --no-reload` and
  `APP_RELOAD` is set to a truthy value
- **THEN** the command starts Uvicorn without reload enabled

### Requirement: Project CLI parser standard
The system SHALL use Click for project-owned command-line entrypoints covered
by this change while preserving their documented command interfaces.

#### Scenario: Click dependency is direct
- **WHEN** project CLI code imports Click
- **THEN** `pyproject.toml` lists Click as a direct runtime dependency

#### Scenario: Validation command keeps existing behaviour
- **WHEN** a developer runs `wevra-validate` with existing targets, verbosity,
  or override options
- **THEN** the command accepts the same options and reports the same validation
  outcomes and exit status as before the command-prefix change

#### Scenario: Validation command implementation is tool-owned
- **WHEN** a developer inspects the `wevra-validate` package script entry point
- **THEN** the command wrapper is provided by `wevra.tools` and discovers
  validation targets from configured modules
