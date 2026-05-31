# application-infrastructure Specification

## Purpose
TBD - created by archiving change init-project. Update Purpose after archive.
## Requirements
### Requirement: Project metadata and toolchain
The system SHALL define Python project metadata in `pyproject.toml` for a Python 3.13+ application managed by `uv` and built with `uv_build`.

#### Scenario: Project metadata exists
- **WHEN** a developer inspects the project root
- **THEN** `pyproject.toml` defines the project name, Python 3.13+ requirement, `uv_build` build backend, runtime dependencies, and development dependency groups

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
The system SHALL use a `src/` package layout with `src/uniquode` as the core importable application package, while allowing feature modules and web resources to live in conventional sibling locations under `src/`.

#### Scenario: Package imports from source layout
- **WHEN** the project is installed or run through `uv`
- **THEN** the `uniquode` package resolves from `src/uniquode`

#### Scenario: Infrastructure modules are separated
- **WHEN** a developer inspects `src/uniquode`
- **THEN** application construction, settings, route registration, models, migrations, and shared infrastructure have explicit package locations or documented module boundaries

#### Scenario: Web resources use global roots
- **WHEN** a developer inspects the source tree
- **THEN** templates and static assets live in conventional global roots under `src/` rather than inside `src/uniquode`

#### Scenario: Feature modules may live beside the core package
- **WHEN** a later capability introduces a feature module such as `site`, `auth`, `api`, or `integrations`
- **THEN** the module may live alongside `src/uniquode` and integrate through the application's route and infrastructure boundaries

### Requirement: ASGI application shell
The system SHALL provide a FastAPI/Starlette ASGI application shell with an application factory and stable ASGI app import path.

#### Scenario: Application can be imported
- **WHEN** a developer imports the documented ASGI app path
- **THEN** the import returns an ASGI-compatible application object using
  default environment-backed settings without requiring product configuration
  or database state

#### Scenario: Application can be constructed for tests
- **WHEN** tests call the application factory with explicit settings
- **THEN** a fresh FastAPI application instance is returned with those settings
  and baseline routes registered

### Requirement: Async-first boundaries
The system SHALL define initial request and integration boundaries as async-first where they may perform I/O.

#### Scenario: Baseline route handlers use async functions
- **WHEN** the initial routes are inspected
- **THEN** request handlers that form the application baseline are declared with `async def`

#### Scenario: Blocking work is not introduced
- **WHEN** the initial application shell is inspected
- **THEN** it does not perform blocking database, network, or filesystem work in request handlers

### Requirement: Persistence conventions
The system SHALL establish SQLAlchemy async persistence conventions with Alembic migrations without coupling route handlers directly to database clients.

#### Scenario: Persistence location is defined
- **WHEN** a developer inspects the project package
- **THEN** there is a clear package location or documented boundary for SQLAlchemy async models, session configuration, and Alembic migrations

#### Scenario: Routes are not coupled to database clients
- **WHEN** the route modules are inspected
- **THEN** route handlers do not directly instantiate or depend on database clients

#### Scenario: PostgreSQL and SQLite remain supported
- **WHEN** a developer inspects persistence configuration
- **THEN** PostgreSQL is supported for production and SQLite is supported for local development and lightweight tests where behaviour remains portable

### Requirement: Template conventions
The system SHALL define the baseline Jinja2 server-rendered template and static asset locations and provide rendering conventions without introducing product-specific UI before requirements need it.

#### Scenario: Template location is configurable
- **WHEN** a developer inspects the project structure or configuration
- **THEN** the Jinja2 template root is supplied through settings with a default value of `src/templates/`

#### Scenario: Static asset location is configurable
- **WHEN** a developer inspects the project structure or configuration
- **THEN** the static asset root is supplied through settings with a default value of `src/static/`

#### Scenario: Static asset route prefix is configurable
- **WHEN** a developer inspects the project structure or configuration
- **THEN** the static asset route prefix is supplied through settings with a default value of `/static/`

#### Scenario: Rendering conventions are explicit
- **WHEN** a developer inspects the web foundation implementation
- **THEN** there is a documented or code-defined rendering helper or boundary that renders templates by path from the configured template root

#### Scenario: HTML dispatch and static serving are separate concerns
- **WHEN** a developer inspects the web foundation implementation
- **THEN** HTML request dispatch and static asset serving are wired as separate mechanisms with distinct configuration and handling boundaries

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
The system SHALL limit runtime dependencies to platform and product dependencies justified by accepted OpenSpec requirements.

#### Scenario: Runtime dependencies are requirement-scoped
- **WHEN** a developer reviews runtime dependencies
- **THEN** they are limited to accepted FastAPI/Starlette, Jinja2, ASGI, SQLAlchemy async, Alembic, FastAPI Users, and requirement-backed product needs

#### Scenario: Dependencies are added through uv project metadata
- **WHEN** dependencies are added during implementation
- **THEN** runtime dependencies are added with `uv add` and development dependencies are added with `uv add --dev` or an appropriate dependency group option

#### Scenario: Virtual environment is not mutated outside project metadata
- **WHEN** implementation needs package inspection
- **THEN** read-only `uv pip` commands are allowed, but `uv pip install` and other `uv pip` commands that modify the virtual environment are not used

#### Scenario: Unrequired product dependencies are excluded
- **WHEN** dependency changes are reviewed
- **THEN** they do not add asset pipeline, queue, NoSQL, or product-specific integration dependencies without a requirement

### Requirement: Validation command explainability
The system SHALL keep quick validation output concise while offering a verbose mode that explains the checks being performed.

#### Scenario: Default validation output remains concise
- **WHEN** a developer runs the validation command without verbosity
- **THEN** the command reports per-target success or failure without listing every individual check

#### Scenario: Verbose validation output lists checks
- **WHEN** a developer runs the validation command with verbose output enabled
- **THEN** the command lists the concrete checks performed for each target, including relevant paths, route/template checks, asset checks, and persistence checks

### Requirement: Server-rendered form CSRF protection
The system SHALL protect all server-rendered form submissions with a shared CSRF mechanism rather than per-view ad hoc checks.

#### Scenario: Form pages receive CSRF tokens
- **WHEN** the application renders a server-owned HTML page or fragment that contains a POST form
- **THEN** the rendered form includes a CSRF field derived from the shared form-security boundary

#### Scenario: Form submissions are checked before view handling
- **WHEN** a browser submits a server-rendered form through a page or partial route
- **THEN** the HTML dispatcher validates the submitted CSRF token before the route view can perform state-changing work

#### Scenario: Non-form unsafe requests can provide a CSRF header
- **WHEN** a page or partial route receives an unsafe method from htmx or custom
  JavaScript without a form field payload
- **THEN** the HTML dispatcher can validate the configured CSRF token from a
  request header instead of requiring a form field

#### Scenario: Invalid CSRF submissions are rejected
- **WHEN** a form submission omits, tampers with, or mismatches the CSRF token
- **THEN** the application rejects the request without issuing authentication cookies or performing the requested state change

#### Scenario: CSRF signing seed is configurable
- **WHEN** the application constructs the CSRF token signer
- **THEN** it uses an application setting for the signing secret, with local development allowed to generate a startup-local secret until environment-backed configuration is introduced

#### Scenario: Non-local CSRF signing seed is stable
- **WHEN** the application is configured for a non-local deployment
- **THEN** the CSRF signing secret must be explicitly configured and non-blank so tokens remain valid across app processes and restarts

#### Scenario: Non-local CSRF cookie transport is secure
- **WHEN** the application is configured for a non-local deployment
- **THEN** CSRF nonce cookies are marked `Secure` so they are not sent over
  plaintext HTTP

### Requirement: Local runtime command
The system SHALL provide a project runtime command named `runserver` for local execution of the ASGI application through `uv`.

#### Scenario: Project script is defined
- **WHEN** a developer inspects `pyproject.toml`
- **THEN** the project metadata defines a `runserver` command

#### Scenario: Runtime command targets the stable ASGI app
- **WHEN** a developer runs the documented local server command
- **THEN** it starts Uvicorn against `uniquode.asgi:app`

#### Scenario: Runtime command is invoked through uv
- **WHEN** local development instructions reference the server startup command
- **THEN** they use `uv run runserver`

### Requirement: Local runtime defaults
The system SHALL define the baseline local runtime behaviour of the `runserver` command for host, port, and reload operation.

#### Scenario: Local runtime uses development-oriented defaults
- **WHEN** a developer runs `uv run runserver` without additional arguments
- **THEN** the application starts with the documented local host, port, and reload defaults

#### Scenario: Local runtime accepts explicit overrides
- **WHEN** a developer runs `uv run runserver` with supported host, port, or reload command-line options
- **THEN** the application starts with the supplied values instead of the baseline defaults

#### Scenario: Reload falls back to environment configuration
- **WHEN** a developer runs `uv run runserver` without `--reload` and `APP_RELOAD` is set to a truthy value
- **THEN** the application starts with reload enabled

#### Scenario: Runtime contract stays independent of front-end tooling
- **WHEN** the local runtime command is reviewed
- **THEN** it does not require a front-end asset pipeline in order to start the ASGI application

### Requirement: Runtime command validation
The system SHALL provide focused validation that the local runtime command wiring remains aligned with the documented ASGI target and startup contract.

#### Scenario: Runtime command wiring is covered
- **WHEN** the project's validation checks are run
- **THEN** at least one focused test or smoke check verifies the configured local runtime command or its equivalent startup contract
