# application-infrastructure Specification

## Purpose
TBD - created by archiving change init-project. Update Purpose after archive.
## Requirements
### Requirement: Project metadata and toolchain
The system SHALL define Python project metadata for a Python 3.13+ application
managed by `uv`, with the repository root acting as a local workspace
coordinator, `app` acting as the buildable application project, and Wybra
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
- **AND** it does not need to re-declare Wybra-owned operator scripts

#### Scenario: Wybra command scripts are package-owned and prefixed
- **WHEN** a developer inspects `wybra/pyproject.toml`
- **THEN** the package exposes `wybra-runserver`, `wybra-migrate`,
  `wybra-routes`, `wybra-validate`, and `wybra-identitymgr`
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
- **THEN** `wybra` is listed as a project dependency
- **AND** the local workspace root may resolve `wybra` from a temporary ignored
  checkout while the framework is not yet available as a regular dependency

#### Scenario: Shared lock controls local dependency resolution
- **WHEN** a developer runs `uv` in the local workspace while `wybra/` is a
  workspace member
- **THEN** `uv` discovers the parent workspace
- **AND** the application and local Wybra dependency source resolve dependency
  versions from the parent `uv.lock`
- **AND** member-local lock files are not used for coordinated workspace
  development

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
The system SHALL use a workspace layout with `app/src/app` as the concrete
application package, while consuming reusable framework infrastructure from an
explicit `wybra` workspace dependency.

#### Scenario: Package imports from source layout
- **WHEN** the project is installed or run through `uv`
- **THEN** the `app` package resolves from `app/src/app`

#### Scenario: Infrastructure modules are external dependency
- **WHEN** a developer inspects the `app` source tree
- **THEN** reusable web infrastructure, data infrastructure, tooling, auth,
  model, migration, template, and static-resource framework code is not
  vendored under `app/src/app`, `app/src/web_ext`, or `app/src/wybra` in the
  application project

#### Scenario: Wybra is a workspace member during local development
- **WHEN** a developer runs the application in the local development workspace
- **THEN** the `wybra` package is provided by an adjacent workspace member
  dependency rather than by application-local source

#### Scenario: Application package excludes framework source
- **WHEN** the `app` project build metadata is inspected
- **THEN** it builds the `app` application package and does not include
  the `wybra` framework package as an application build module

#### Scenario: Web resources are module-owned
- **WHEN** a developer inspects the source tree or workspace dependencies
- **THEN** templates and static assets live in configured module package roots
  such as `src/<module>/templates/` and `src/<module>/static/`

#### Scenario: Feature modules may live beside the core package
- **WHEN** a later capability introduces an application feature module
- **THEN** the module may live alongside `app/src/app` in the application
  project and integrate through the configured module boundaries

### Requirement: Wybra framework namespace
The system SHALL move reusable framework infrastructure into an explicit
`wybra` package namespace while keeping `app` as the concrete host
application package.

#### Scenario: Reusable infrastructure uses the framework namespace
- **WHEN** the reusable web, data, settings, tooling, and auth infrastructure is
  inspected after the namespace refactor
- **THEN** those reusable packages are imported through `wybra.*` package paths
  rather than temporary top-level infrastructure package names or the
  `uniquode` application package

#### Scenario: Host application remains separate
- **WHEN** a developer inspects the `app` package after the namespace
  refactor
- **THEN** it contains application policy, settings adapters, startup wiring,
  health routes, and application-specific validation rather than reusable
  framework infrastructure

#### Scenario: Behaviour is preserved through the namespace refactor
- **WHEN** the namespace refactor is applied
- **THEN** runtime startup, route composition, template rendering, static asset
  serving, validation, migration commands, and migration graph behaviour remain
  equivalent apart from documented import path, package data, and configured
  module name changes

#### Scenario: Compatibility shims are explicit
- **WHEN** the namespace refactor design is completed
- **THEN** any temporary compatibility shim is justified by a concrete consumer
  requirement rather than being introduced by default

### Requirement: ASGI application shell
The system SHALL provide a FastAPI/Starlette ASGI application shell with an
application factory and stable ASGI app import path.

#### Scenario: Application import requires resolved configuration
- **WHEN** a developer imports the documented ASGI app path for normal default
  startup
- **THEN** the import resolves application configuration through `APP_CONFIG` or
  the host project's `app.toml`
- **AND** missing application configuration fails with an actionable
  configuration error instead of starting with built-in defaults
- **AND** importing the app does not require database schema state

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
- **THEN** there is a clear package location or documented boundary for
  SQLAlchemy async models, database URL handling, session configuration,
  Alembic migration infrastructure, and module-owned migration revisions

#### Scenario: Models modules contain ORM models
- **WHEN** a package exposes a `models` module
- **THEN** that module is reserved for SQLAlchemy ORM models and migration metadata rather than unrelated domain objects, schemas, or service contracts

#### Scenario: Migration metadata is discovered from configured modules
- **WHEN** Alembic migration metadata is built
- **THEN** `wybra.db` derives conventional `<module>.models` packages from
  configured modules and reads their exported `metadata` objects

#### Scenario: Optional package models are explicit
- **WHEN** optional reusable packages provide SQLAlchemy models
- **THEN** their model metadata is included in migrations only when the host
  application explicitly enables that package module

#### Scenario: Module migration revisions are explicit
- **WHEN** optional reusable packages provide SQLAlchemy models and migration
  revisions
- **THEN** their migration version locations are included only when the host
  application explicitly enables that package module

#### Scenario: Routes are not coupled to database clients
- **WHEN** the route modules are inspected
- **THEN** route handlers do not directly instantiate or depend on database clients

#### Scenario: PostgreSQL and SQLite remain supported
- **WHEN** a developer inspects persistence configuration
- **THEN** PostgreSQL is supported for production and SQLite is supported for local development and lightweight tests where behaviour remains portable

#### Scenario: Data infrastructure helpers are reusable
- **WHEN** application startup, migration tooling, validation, or tests need
  database URL parsing, database URL resolution, async engine creation, session
  factory creation, or session scope helpers
- **THEN** those helpers are provided by `wybra.db` rather than by the
  `uniquode` application package

#### Scenario: Migration command settings are injected
- **WHEN** generic migration command infrastructure needs application settings,
  default modules, or the default database URL
- **THEN** a host adapter supplies those values instead of `wybra.db` importing
  the `uniquode` application package

#### Scenario: Module surface conventions are centralised
- **WHEN** reusable web, data, and tooling layers need conventional configured
  module surface names or export attribute names
- **THEN** those strings are defined in one reusable convention module rather
  than being duplicated across discovery implementations

### Requirement: Template conventions
The system SHALL define baseline Jinja2 server-rendered template and static
asset conventions through configured module package sources without introducing
product-specific UI before requirements need it.

#### Scenario: Template sources are module-owned
- **WHEN** a developer inspects the project structure or configuration
- **THEN** templates are discovered from configured module package sources such
  as `src/<module>/templates/`

#### Scenario: Static asset sources are module-owned
- **WHEN** a developer inspects the project structure or configuration
- **THEN** static assets are discovered from configured module package sources
  such as `src/<module>/static/`

#### Scenario: Omitted web core static defaults are not served
- **WHEN** `wybra.web` is not included in the configured module list and no
  explicit filesystem static root is configured
- **THEN** application static serving does not fall back to `wybra.web` package
  assets

#### Scenario: Empty static mount preserves URL generation
- **WHEN** no configured module contributes static assets and no explicit
  filesystem static root is configured
- **THEN** the application still provides the configured static route name for
  URL generation, while requests for assets return a normal missing-asset
  response

#### Scenario: Static asset route prefix is configurable
- **WHEN** a developer inspects the project structure or configuration
- **THEN** the static asset route prefix is supplied through settings with a default value of `/static/`

#### Scenario: Rendering conventions are explicit
- **WHEN** a developer inspects the web foundation implementation
- **THEN** there is a documented or code-defined rendering helper or boundary
  that renders templates by logical path from the composed template namespace

#### Scenario: HTML dispatch and static serving are separate concerns
- **WHEN** a developer inspects the web foundation implementation
- **THEN** HTML request dispatch and static asset serving are wired as separate mechanisms with distinct configuration and handling boundaries

### Requirement: Baseline validation commands
The system SHALL provide repeatable baseline validation commands for
formatting, linting, type checking, and tests.

#### Scenario: Application validation runs against workspace framework
- **WHEN** a developer runs the application validation suite from the `app`
  member directory
- **THEN** it imports `wybra` from the adjacent workspace member dependency and
  verifies application integration with that framework dependency

#### Scenario: Framework tests are not duplicated in application
- **WHEN** framework-specific web, data, auth, tooling, or namespace tests are
  inspected
- **THEN** they live in the `wybra` project rather than in the `app`
  application test suite

#### Scenario: Application repository does not validate framework internals
- **WHEN** repository CI or pre-commit validation runs for `uniquode`
- **THEN** it validates application formatting, linting, type checking, and
  tests
- **AND** it does not run Wybra-owned tests, linting, type checks, or
  package-build checks

#### Scenario: Pre-commit runs application validation
- **WHEN** pre-commit hooks run in the `uniquode` repository
- **THEN** they include the `wybra-validate` command as a configuration and
  composition backstop
- **AND** that hook runs with `app` as the host project directory

#### Scenario: Application tests retain integration coverage
- **WHEN** the `app` test suite is inspected
- **THEN** it retains focused tests for application settings, startup,
  configured module loading, app routes, app templates, and Wybra command
  adapters used by the host project

#### Scenario: OpenSpec remains application-owned
- **WHEN** the `wybra` project is extracted into its own repository
- **THEN** OpenSpec artifacts remain in the `uniquode` repository
- **AND** the `wybra` repository does not initialise or copy a separate
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

### Requirement: Dependency discipline
The system SHALL limit runtime dependencies to platform and product dependencies justified by accepted OpenSpec requirements.

#### Scenario: Runtime dependencies are requirement-scoped
- **WHEN** a developer reviews runtime dependencies
- **THEN** they are limited to accepted FastAPI/Starlette, Jinja2, ASGI,
  SQLAlchemy async, Alembic, FastAPI Users, Click, and requirement-backed
  product needs

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
The system SHALL provide a package-owned runtime command named
`wybra-runserver` for local execution of the configured host ASGI application
through `uv`.

#### Scenario: Prefixed package script is defined
- **WHEN** a developer inspects `wybra/pyproject.toml`
- **THEN** the project metadata defines a `wybra-runserver` command

#### Scenario: Host application supplies the stable ASGI app target
- **WHEN** a developer runs the documented local server command
- **THEN** Wybra resolves the host project metadata
- **AND** it starts Uvicorn against the configured host ASGI application target

#### Scenario: Runtime command implementation is tool-owned
- **WHEN** a developer inspects the `wybra-runserver` package script entry point
- **THEN** the command wrapper is provided by `wybra.tools`
  while still targeting the configured host application

#### Scenario: Runtime command is invoked through uv
- **WHEN** local development instructions reference the server startup command
- **THEN** they use `uv run wybra-runserver`

### Requirement: Local runtime defaults
The system SHALL define the baseline local runtime behaviour of the
`wybra-runserver` command for host, port, and reload operation.

#### Scenario: Local runtime uses development-oriented defaults
- **WHEN** a developer runs `uv run wybra-runserver` without additional
  arguments
- **THEN** the application starts with the documented local host, port, and
  reload defaults

#### Scenario: Local runtime accepts explicit overrides
- **WHEN** a developer runs `uv run wybra-runserver` with supported host, port,
  or reload command-line options
- **THEN** the application starts with the supplied values instead of the
  baseline defaults

#### Scenario: Reload falls back to environment configuration
- **WHEN** a developer runs `uv run wybra-runserver` without `--reload` and
  `APP_RELOAD` is set to a truthy value
- **THEN** the application starts with reload enabled

#### Scenario: Runtime contract stays independent of front-end tooling
- **WHEN** the local runtime command is reviewed
- **THEN** it does not require a front-end asset pipeline in order to start the
  ASGI application

### Requirement: Runtime command validation
The system SHALL provide focused validation that the local runtime command wiring remains aligned with the documented ASGI target and startup contract.

#### Scenario: Runtime command wiring is covered
- **WHEN** the project's validation checks are run
- **THEN** at least one focused test or smoke check verifies the configured local runtime command or its equivalent startup contract

### Requirement: Runtime command Uvicorn pass-through
The system SHALL allow the `wybra-runserver` command to forward additional
command-line arguments to Uvicorn after a `--` separator while preserving the
configured host ASGI target and local runtime defaults.

#### Scenario: Uvicorn arguments are forwarded
- **WHEN** a developer runs
  `uv run wybra-runserver -- --forwarded-allow-ips 127.0.0.1`
- **THEN** the command invokes Uvicorn for the configured host ASGI application
  with `--forwarded-allow-ips 127.0.0.1`

#### Scenario: Project runtime options still apply
- **WHEN** a developer runs
  `uv run wybra-runserver --host 0.0.0.0 --port 9000 -- --proxy-headers`
- **THEN** the command applies the project `--host` and `--port` options and
  passes `--proxy-headers` through to Uvicorn

#### Scenario: Application target remains project-owned
- **WHEN** a developer runs `uv run wybra-runserver -- other.asgi:app`
- **THEN** the command rejects the extra application target instead of passing
  two positional application targets to Uvicorn

#### Scenario: Reload environment fallback remains available
- **WHEN** a developer runs `uv run wybra-runserver -- <uvicorn args>` without
  the project `--reload` option and `APP_RELOAD` is set to a truthy value
- **THEN** the command starts Uvicorn with reload enabled and preserves the
  supplied Uvicorn arguments

#### Scenario: Reload environment fallback can be disabled explicitly
- **WHEN** a developer runs `uv run wybra-runserver --no-reload` and
  `APP_RELOAD` is set to a truthy value
- **THEN** the command starts Uvicorn without reload enabled

### Requirement: Project CLI parser standard
The system SHALL use Click for project-owned command-line entrypoints covered
by this change while preserving their documented command interfaces.

#### Scenario: Click dependency is direct
- **WHEN** project CLI code imports Click
- **THEN** `pyproject.toml` lists Click as a direct runtime dependency

#### Scenario: Validation command keeps existing behaviour
- **WHEN** a developer runs `wybra-validate` with existing targets, verbosity,
  or override options
- **THEN** the command accepts the same options and reports the same validation
  outcomes and exit status as before the command-prefix change

#### Scenario: Validation command implementation is tool-owned
- **WHEN** a developer inspects the `wybra-validate` package script entry point
- **THEN** the command wrapper is provided by `wybra.tools` and discovers
  validation targets from configured modules

### Requirement: Project command configuration boundary
The system SHALL make package-owned Wybra project commands resolve the concrete
host application project and application config before constructing normal
runtime settings.

#### Scenario: Command invoked from app project
- **WHEN** an operator runs a package-owned Wybra project command from the host
  application project directory
- **THEN** the command resolves that project and its `app.toml` as the
  application config boundary

#### Scenario: Command invoked from workspace root
- **WHEN** an operator runs a package-owned Wybra project command from a
  workspace root that unambiguously contains one configured Wybra host
  application project
- **THEN** the command resolves that host application project and its `app.toml`
  as the application config boundary

#### Scenario: Command cannot resolve app config
- **WHEN** a package-owned Wybra project command cannot resolve an application
  config file through `APP_CONFIG` or project discovery
- **THEN** the command fails with an actionable configuration error
- **AND** it does not continue with baked-in default settings

#### Scenario: Host app remains separate from reusable package
- **WHEN** Wybra project commands resolve the host application config
- **THEN** they use reusable project metadata and config-loading contracts
  rather than importing `uniquode.io` application modules directly

#### Scenario: Application config uses namespaced app tables
- **WHEN** a host application defines app-wide modules, routes, templates,
  static settings, or database configuration
- **THEN** those values live under `[app]`, `[app.routes]`, `[app.templates]`,
  and `[app.static]` rather than as global config tables

#### Scenario: Route module aliases are normalised
- **WHEN** `[app.routes]` contains a module key with hyphens such as
  `wybra-auth`
- **THEN** the route prefix mapping is applied to the dotted Python module name
  `wybra.auth`
- **AND** route labels inside that module mapping are not normalised

#### Scenario: Route module alias collisions are rejected
- **WHEN** `[app.routes]` contains multiple keys that normalise to the same
  Python module name
- **THEN** application config loading fails with a configuration error

### Requirement: Host application uses Wybra site startup
The host application SHALL use the public Wybra site startup API for Wybra-owned composition while retaining ownership of host-specific application behaviour.

#### Scenario: Host startup delegates Wybra concerns
- **WHEN** the host ASGI application is constructed
- **THEN** the host app creates or receives its FastAPI app instance
- **AND** delegates Wybra module, route, auth, database, and settings composition to Wybra startup

#### Scenario: Host app excludes Wybra internals
- **WHEN** the host app source is inspected
- **THEN** it does not construct Wybra auth runtime state, database runtime state, module route defaults, or module settings internals directly

#### Scenario: Host app keeps product routes
- **WHEN** product-specific pages or routes are required
- **THEN** their handlers, views, and route-surface declarations remain in the host app or host-owned modules
- **AND** Wybra discovers and registers those route surfaces from the configured module list
- **AND** the host app does not call route discovery or registration boilerplate itself
- **AND** route handlers use Wybra through public startup and type-keyed capability APIs only

### Requirement: App tests respect Wybra ownership
The host application test suite SHALL cover app-owned integration with the Wybra site startup API without duplicating Wybra module internals.

#### Scenario: App tests startup integration
- **WHEN** the host app test suite validates startup
- **THEN** it asserts that app-owned routes and configuration integrate with the public Wybra startup API
- **AND** it does not test Wybra auth, database, settings, or route composition semantics as if they were app-owned

#### Scenario: Wybra tests framework composition
- **WHEN** framework startup composition semantics are tested
- **THEN** those tests live in the Wybra project or Wybra-owned test suite
- **AND** the host app tests only rely on the documented public API

### Requirement: Host app contains only app-owned site code
The host app SHALL contain only app-specific startup, route surfaces, views, context, and product settings. Generic Wybra configuration, environment loading, validation, module setup, database/auth/web setup, route discovery, route registration, static composition, and template composition SHALL be owned by Wybra or by the configured module that owns the concern.

#### Scenario: Basic app has no Wybra environment adapter
- **WHEN** a basic Wybra host app is inspected
- **THEN** it does not require an app-owned `environment.py` or equivalent wrapper to load Wybra configuration
- **AND** Wybra-owned tools load environment/configuration through Wybra-owned sources or explicit configured module definitions

#### Scenario: Basic app has no Wybra config aggregation file
- **WHEN** a basic Wybra host app is inspected
- **THEN** it does not require an app-owned `config_definitions.py` file for Wybra-owned settings
- **AND** reusable configuration definitions are declared by Wybra or the owning module

#### Scenario: App can omit database and auth modules
- **WHEN** app configuration omits `wybra.db` or `wybra.auth`
- **THEN** startup does not register database or auth capabilities for the omitted modules
- **AND** startup does not synthesise fallback database or auth configuration

#### Scenario: App tests cover app ownership only
- **WHEN** app tests inspect startup and settings behaviour
- **THEN** they assert app-owned route, view, context, and product settings outcomes
- **AND** they do not duplicate Wybra-owned config, environment, auth, database, static, or template internals

### Requirement: Basic app exposes app-owned route, view, context, and validation examples
A cleaned basic app SHALL keep app-owned route assembly, view handlers, request context helpers, and product validation in small explicit modules without framework boilerplate packages.

#### Scenario: Home page view is app-owned
- **WHEN** the app route surface is inspected
- **THEN** the home page handler lives in the app view module
- **AND** route assembly registers that handler through the app route module

#### Scenario: Home context is app-owned
- **WHEN** the home page view needs product context
- **THEN** the context helper lives in the app context module

#### Scenario: App validation is product-specific
- **WHEN** the app exposes validation targets
- **THEN** they validate app-owned product concerns such as the home route, health route, home page template, and static assets
- **AND** they do not validate Wybra-owned environment, database, auth, static, template, or route composition internals

#### Scenario: Health endpoint is included in the basic app
- **WHEN** a basic app route surface is generated or inspected
- **THEN** it includes a simple app-owned health endpoint

#### Scenario: Optional app setup hook is visible
- **WHEN** a basic app module is generated or inspected
- **THEN** it exposes a documented no-op `setup_site` hook from the app startup module
- **AND** the documentation explains that the stub is optional and may be removed when the app has no app-specific startup work

#### Scenario: App context provider composes request template context
- **WHEN** the basic app contributes template context
- **THEN** it exposes a context provider that accepts the request and existing template context
- **AND** it returns a new template context containing app-owned additions
- **AND** it does not mutate a raw context dictionary in place

### Requirement: Wybra owns reusable web request and static setup
Wybra SHALL own reusable template request context setup and runtime static file serving for composed sites.

#### Scenario: Request context is provided by default
- **WHEN** Wybra web setup handles a template-rendering request
- **THEN** the immutable per-request template context includes the current request by default
- **AND** templates can inspect request URL, path, and connection attributes

#### Scenario: Template context providers accumulate immutably
- **WHEN** Wybra assembles template context providers for a request
- **THEN** it initialises an empty `TemplateContext`
- **AND** each provider receives the request and current `TemplateContext`
- **AND** each provider returns a new `TemplateContext`
- **AND** the final render boundary converts the accumulated context to a plain mapping for templates

#### Scenario: Request context can be disabled
- **WHEN** the Wybra web request-context setting is explicitly disabled
- **THEN** Wybra does not inject the current request into template context

#### Scenario: Filesystem static handling is Wybra-owned
- **WHEN** a static root is configured
- **THEN** Wybra constructs the runtime static file ASGI app
- **AND** the host app does not construct or inject `StaticFiles`

#### Scenario: No static root means no filesystem static serving
- **WHEN** no static root is configured
- **THEN** Wybra does not enable filesystem static serving for the host app

#### Scenario: ASGI loading is delegated to Wybra
- **WHEN** a host app exposes its ASGI application
- **THEN** the app entry point delegates common loading and configuration-error reporting to Wybra
- **AND** the app entry point contains only app-factory import and the Wybra loader call
