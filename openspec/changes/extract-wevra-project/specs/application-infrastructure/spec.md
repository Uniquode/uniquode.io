## MODIFIED Requirements

### Requirement: Source package layout
The system SHALL use a `src/` package layout with `src/uniquode` as the
concrete application package, while consuming reusable framework infrastructure
from an explicit `wevra` project dependency.

#### Scenario: Package imports from source layout
- **WHEN** the project is installed or run through `uv`
- **THEN** the `uniquode` package resolves from `src/uniquode`

#### Scenario: Infrastructure modules are external dependency
- **WHEN** a developer inspects the `uniquode` source tree
- **THEN** reusable web infrastructure, data infrastructure, tooling, auth,
  model, migration, template, and static-resource framework code is not
  vendored under `src/uniquode` or `src/wevra` in the application project

#### Scenario: Wevra is editable during local development
- **WHEN** a developer runs the application in the local development checkout
- **THEN** the `wevra` package is provided by an editable adjacent project
  dependency rather than by application-local source

#### Scenario: Application package excludes framework source
- **WHEN** the `uniquode` project build metadata is inspected
- **THEN** it builds the `uniquode` application package and does not include
  the `wevra` framework package as an application build module

#### Scenario: Web resources are module-owned
- **WHEN** a developer inspects the source tree or editable dependencies
- **THEN** templates and static assets live in configured module package roots
  such as `src/<module>/templates/` and `src/<module>/static/`

#### Scenario: Feature modules may live beside the core package
- **WHEN** a later capability introduces an application feature module
- **THEN** the module may live alongside `src/uniquode` in the application
  project and integrate through the configured module boundaries

### Requirement: Project metadata and toolchain
The system SHALL define Python project metadata in `pyproject.toml` for a
Python 3.13+ application managed by `uv` and built with `uv_build`.

#### Scenario: Project metadata exists
- **WHEN** a developer inspects the project root
- **THEN** `pyproject.toml` defines the project name, Python 3.13+ requirement,
  `uv_build` build backend, runtime dependencies, and development dependency
  groups

#### Scenario: Editable framework dependency is declared
- **WHEN** a developer inspects `uniquode` dependency metadata
- **THEN** `wevra` is listed as a project dependency and resolved from an
  editable adjacent path source for local development

#### Scenario: Tool configuration is discoverable
- **WHEN** a developer inspects `pyproject.toml`
- **THEN** configuration for Ruff, `ty`, and pytest is present or the file
  documents the command conventions needed to run them

### Requirement: Baseline validation commands
The system SHALL provide repeatable baseline validation commands for formatting,
linting, type checking, and tests.

#### Scenario: Application validation runs against editable framework
- **WHEN** a developer runs the `uniquode` validation suite
- **THEN** it imports `wevra` from the editable adjacent project dependency and
  verifies application integration with that framework dependency

#### Scenario: Framework tests are not duplicated in application
- **WHEN** framework-specific web, data, auth, tooling, or namespace tests are
  inspected
- **THEN** they live in the `wevra` project rather than in the `uniquode`
  application test suite

#### Scenario: Application tests retain integration coverage
- **WHEN** the `uniquode` test suite is inspected
- **THEN** it retains focused tests for application settings, startup,
  configured module loading, app routes, app templates, and project command
  adapters that depend on `wevra`
