## Context

The project is being initialized from an accepted platform baseline recorded in ADR 0001. The baseline selects Python 3.14, FastAPI/Starlette, async-first ASGI, Jinja2 for server-rendered templates, `uv`, `uv_build`, Ruff, `ty`, pytest, PostgreSQL/SQLite, and Tortoise ORM.

The repository currently contains OpenSpec artifacts and project guidance, but not the Python application package. This change turns the platform decisions into an initial project structure that future product requirements can build on. The design must establish enough infrastructure for repeatable development while avoiding product features, domain models, or front-end implementation before requirements need them.

Primary stakeholders are project maintainers and AI/code agents working from the OpenSpec workflow. The design should make the expected project shape, command surface, and dependency boundaries explicit so later changes can be small and requirement-driven.

## Goals / Non-Goals

**Goals:**

- Define a Python 3.14 project managed by `uv` with `uv_build` as the build backend.
- Use a `src/` layout with `src/uniquode` as the importable application package.
- Provide a FastAPI/Starlette ASGI application shell with async-first lifecycle and route conventions.
- Establish package boundaries for settings, routes, models, migrations, and future templates.
- Configure baseline development checks for formatting, linting, type checking, and tests.
- Add only platform-level runtime dependencies that are already justified by ADR 0001.
- Leave clear extension points for persistence, migrations, and server-rendered templates without implementing product behavior.

**Non-Goals:**

- Implementing product features, user workflows, or domain-specific routes.
- Creating database-backed domain models beyond placeholder package structure.
- Adding front-end templates, static assets, or styling before UI requirements exist.
- Introducing NoSQL support or backend portability across unrelated storage engines.
- Adding a richer client-side JavaScript application.
- Proving every Tortoise ORM validation-spike concern in this initialization change unless captured as an explicit requirement.

## Decisions

### Use `pyproject.toml` as the project control plane

The project will be initialized through `uv`, which will create `pyproject.toml` and initialize the Git repository as part of project setup. After `uv` creates the project metadata, implementation can edit `pyproject.toml` to align build backend, dependencies, dependency groups, and tool configuration with ADR 0001.

Rationale: This keeps the project bootstrap discoverable, lets `uv` perform its expected setup work, and avoids bypassing project initialization behavior such as Git repository creation. The resulting `pyproject.toml` remains the control plane for package metadata, Python version requirements, build backend, dependencies, optional development dependencies, and tool configuration.

Alternatives considered:

- Writing `pyproject.toml` directly: rejected because it can skip setup behavior provided by `uv`, including repository initialization.
- Separate tool-specific configuration files: useful for large configurations, but premature for the initial project.
- `setup.py` or `setup.cfg`: less aligned with the selected `uv_build` backend and modern Python packaging.

### Keep source artifacts trackable and generated files ignored

The project `.gitignore` should ignore generated Python artifacts, local environments, tool caches, build outputs, local environment files, and local database files. It should not ignore `openspec/`, because OpenSpec artifacts are part of the project source of truth. It should not ignore `.agents/`, because project-local agent skills and instructions may be tracked with the source when useful.

Rationale: The repository should preserve architecture records, OpenSpec changes, and project-local agent guidance while excluding generated or machine-local files.

Alternatives considered:

- Ignore all agent directories: rejected for `.agents/` because this project uses `.agents/skills` as project-local workflow assets.
- Ignore OpenSpec artifacts as planning output: rejected because this project treats OpenSpec artifacts and ADRs as source-controlled project records.

### Keep runtime dependencies limited to accepted platform dependencies

Initial runtime dependencies will be limited to the FastAPI/Starlette ASGI stack, Jinja2 template support, and Tortoise ORM/database integration required by ADR 0001. Development tools such as Ruff, `ty`, and pytest belong in development dependency groups. Dependency changes should be made through `uv add` for runtime packages and `uv add --dev` or the appropriate dependency group option for development packages.

Rationale: The proposal explicitly requires dependency discipline. Platform dependencies are justified because they define the application baseline; product-specific libraries are not. Using `uv add` keeps dependency changes reflected in project metadata and avoids virtual-environment-only installs.

Alternatives considered:

- Use `uv pip install` to mutate the virtual environment: rejected because packages can become orphaned from project metadata, making the environment non-reproducible. Read-only `uv pip` inspection remains acceptable.
- Add common web conveniences up front, such as form helpers, authentication libraries, or asset pipelines: rejected until requirements justify them.
- Delay all runtime dependencies: rejected because the purpose of this change is to establish the selected application platform.

### Use a `src/uniquode` package with explicit infrastructure modules

The package will use `src/uniquode` as its root. Initial modules should separate application construction, settings, routing, models, and persistence/migration conventions. A likely shape is:

- `src/uniquode/asgi.py` or `src/uniquode/app.py` for application construction and ASGI exposure.
- `src/uniquode/settings.py` for configuration loading boundaries.
- `src/uniquode/routes/` for route registration.
- `src/uniquode/models/` for future Tortoise models.
- `src/uniquode/migrations/` for migration artifacts or migration integration.
- `src/uniquode/templates/` or a top-level `templates/` convention documented for future Jinja2 work.

Rationale: A `src/` layout prevents accidental imports from the repository root and makes packaging behavior closer to installed behavior. Explicit infrastructure modules make it harder for route handlers to grow direct database or configuration coupling.

Alternatives considered:

- Flat package at repository root: simpler initially, but easier to accidentally depend on the working directory.
- A deep layered architecture immediately: premature before domain requirements exist.

### Expose an application factory and ASGI app object

The initial app should provide a function that constructs the FastAPI application and a module-level ASGI application object for servers and tests. Route registration should happen through a small, explicit function or router module.

Rationale: A factory keeps tests and future configuration overrides straightforward, while a module-level ASGI object gives deployment tools a stable import path.

Alternatives considered:

- Only a module-level app object: simpler, but less flexible for tests and future settings overrides.
- A larger dependency-injection container: unnecessary before domain services exist.

### Keep route handlers async-first

Initial route handlers and extension points will use `async def` where they may touch I/O now or later. Synchronous helpers may exist only when they are CPU-local and do not block the event loop.

Rationale: ADR 0001 defines async-first as a governing constraint. Starting with async route and service boundaries avoids churn when persistence and integrations are added.

Alternatives considered:

- Use synchronous handlers until I/O is added: FastAPI supports this, but it weakens the project-wide async boundary and invites blocking patterns.

### Define persistence boundaries without implementing domain persistence

The initialization should create the package locations and configuration pattern for Tortoise ORM, but avoid real domain models until requirements define them. Database initialization should be designed for FastAPI lifespan integration, with route handlers insulated from direct database-client access.

Rationale: ADR 0001 selects Tortoise ORM and requires persistence to sit behind application services or repository-style modules where useful. The initial project can reserve the boundary without inventing a domain.

Alternatives considered:

- Add a sample model and migration: useful as a spike, but it creates artificial domain surface unless a requirement asks for it.
- Defer all persistence structure: would leave an accepted platform decision without a clear place to land.

### Configure checks as first-class project commands

The project should define repeatable commands or documented command conventions for:

- `uv run ruff format`
- `uv run ruff check`
- `uv run ty check src/`
- `uv run pytest`

Rationale: The checks are part of ADR 0001 and should be available from the start so later changes have a stable validation path.

Alternatives considered:

- Rely on ad hoc tool invocation: works locally, but makes handoffs and agent work less reliable.
- Add extra check tools such as coverage gates immediately: useful later, but not required for initialization.

## Risks / Trade-offs

- [Risk] Python 3.14 or selected tools may have ecosystem friction while still new. Mitigation: keep dependencies minimal, pin compatible versions through `uv`, and isolate tool configuration in `pyproject.toml`.
- [Risk] Tortoise ORM may fail the ADR validation spike, especially around migrations, relationships, or type-checker friction. Mitigation: keep persistence boundaries thin and preserve the ADR fallback to SQLAlchemy 2 async with Alembic.
- [Risk] Creating too much scaffold can imply architecture that requirements have not justified. Mitigation: create only package boundaries and minimal app wiring, leaving product modules empty or absent until needed.
- [Risk] SQLite behavior may diverge from PostgreSQL for future tests. Mitigation: document SQLite as local/lightweight only and require PostgreSQL-backed tests for PostgreSQL-specific behavior.
- [Risk] Jinja2 template conventions may be chosen before UI needs are known. Mitigation: define location and async-rendering expectations without adding template content.

## Migration Plan

This is an initial project setup, so there is no production migration or user data migration.

Implementation should proceed by adding project metadata, creating the `src/uniquode` package, adding the minimal ASGI shell, configuring checks, and adding focused tests that prove the app can be imported and served at the application boundary.

Rollback is straightforward before product code depends on the package: remove the newly added project metadata and source package files. After later changes depend on this structure, rollback should happen through a follow-up OpenSpec change rather than deleting the foundation directly.

## Open Questions

- What exact ASGI import path should deployment documentation standardize on: `uniquode.asgi:app` or `uniquode.app:app`?
- Should template files live inside `src/uniquode/templates` for package-relative loading or at a repository-level `templates/` directory for operational visibility?
- Should migration artifacts live under the Python package or a repository-level migrations directory once Tortoise migration tooling is validated?
