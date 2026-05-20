# application-infrastructure Specification

## Purpose
TBD - created by archiving change init-project. Update Purpose after archive.
## Requirements
### Requirement: Project metadata and toolchain
The system SHALL define Python project metadata in `pyproject.toml` for a Python 3.14 application managed by `uv` and built with `uv_build`.

#### Scenario: Project metadata exists
- **WHEN** a developer inspects the project root
- **THEN** `pyproject.toml` defines the project name, Python 3.14 requirement, `uv_build` build backend, runtime dependencies, and development dependency groups

#### Scenario: Project is initialized through uv
- **WHEN** the initialization implementation creates `pyproject.toml`
- **THEN** it uses `uv` project initialization rather than writing `pyproject.toml` directly

#### Scenario: Git repository is initialized by project tooling
- **WHEN** project initialization completes
- **THEN** the repository has a Git repository initialized by `uv` project setup

#### Scenario: Tool configuration is discoverable
- **WHEN** a developer inspects `pyproject.toml`
- **THEN** configuration for Ruff, `ty`, and pytest is present or the file documents the command conventions needed to run them

### Requirement: Version control ignore policy
The system SHALL define `.gitignore` entries appropriate for the Python project while keeping source and OpenSpec artifacts trackable.

#### Scenario: Python generated files are ignored
- **WHEN** a developer inspects `.gitignore`
- **THEN** it ignores Python caches, test/tool caches, build outputs, virtual environments, local environment files, and local database files

#### Scenario: OpenSpec artifacts are tracked
- **WHEN** a developer inspects `.gitignore`
- **THEN** it does not ignore `openspec/`

#### Scenario: Agent project assets are trackable
- **WHEN** a developer inspects `.gitignore`
- **THEN** it does not ignore `.agents/`

### Requirement: Source package layout
The system SHALL use a `src/` package layout with `src/uniquode` as the importable application package.

#### Scenario: Package imports from source layout
- **WHEN** the project is installed or run through `uv`
- **THEN** the `uniquode` package resolves from `src/uniquode`

#### Scenario: Infrastructure modules are separated
- **WHEN** a developer inspects `src/uniquode`
- **THEN** application construction, settings, route registration, models, migrations, and template conventions have explicit package locations or documented module boundaries

### Requirement: ASGI application shell
The system SHALL provide a FastAPI/Starlette ASGI application shell with an application factory and stable ASGI app import path.

#### Scenario: Application can be imported
- **WHEN** a developer imports the documented ASGI app path
- **THEN** the import returns an ASGI-compatible application object without requiring product configuration or database state

#### Scenario: Application can be constructed for tests
- **WHEN** tests call the application factory
- **THEN** a fresh FastAPI application instance is returned with baseline routes registered

### Requirement: Async-first boundaries
The system SHALL define initial request and integration boundaries as async-first where they may perform I/O.

#### Scenario: Baseline route handlers use async functions
- **WHEN** the initial routes are inspected
- **THEN** request handlers that form the application baseline are declared with `async def`

#### Scenario: Blocking work is not introduced
- **WHEN** the initial application shell is inspected
- **THEN** it does not perform blocking database, network, or filesystem work in request handlers

### Requirement: Persistence conventions
The system SHALL establish Tortoise ORM persistence conventions without introducing product-specific domain models.

#### Scenario: Persistence location is defined
- **WHEN** a developer inspects the project package
- **THEN** there is a clear package location or documented boundary for future Tortoise models and migrations

#### Scenario: Routes are not coupled to database clients
- **WHEN** the initial route modules are inspected
- **THEN** route handlers do not directly instantiate or depend on database clients

### Requirement: Template conventions
The system SHALL define where future Jinja2 server-rendered templates will live without implementing UI templates before requirements need them.

#### Scenario: Template location is documented
- **WHEN** a developer inspects the project structure or configuration
- **THEN** the expected location for future Jinja2 templates is clear

#### Scenario: No product UI is introduced
- **WHEN** the initialization change is reviewed
- **THEN** it does not add product-specific templates, static assets, or front-end behavior

### Requirement: Baseline validation commands
The system SHALL provide repeatable baseline validation commands for formatting, linting, type checking, and tests.

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

### Requirement: Dependency discipline
The system SHALL limit initial runtime dependencies to platform dependencies justified by ADR 0001.

#### Scenario: Runtime dependencies are platform-scoped
- **WHEN** a developer reviews runtime dependencies
- **THEN** they are limited to the accepted FastAPI/Starlette, Jinja2, ASGI, and Tortoise ORM platform needs

#### Scenario: Dependencies are added through uv project metadata
- **WHEN** dependencies are added during implementation
- **THEN** runtime dependencies are added with `uv add` and development dependencies are added with `uv add --dev` or an appropriate dependency group option

#### Scenario: Virtual environment is not mutated outside project metadata
- **WHEN** implementation needs package inspection
- **THEN** read-only `uv pip` commands are allowed, but `uv pip install` and other `uv pip` commands that modify the virtual environment are not used

#### Scenario: Product dependencies are excluded
- **WHEN** the initialization change is reviewed
- **THEN** it does not add authentication, asset pipeline, form handling, queue, NoSQL, or product-specific integration dependencies without a requirement
