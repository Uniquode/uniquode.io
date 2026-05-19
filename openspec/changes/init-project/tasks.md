## 1. Project Metadata

- [x] 1.1 Initialize the project with `uv` so `pyproject.toml` and the Git repository are created by project tooling.
- [x] 1.2 Configure `pyproject.toml` with project metadata, Python 3.14 requirement, and `uv_build` build backend.
- [x] 1.3 Add platform runtime dependencies with `uv add` for the accepted FastAPI/Starlette, Jinja2, ASGI, and Tortoise ORM baseline only.
- [x] 1.4 Add development dependency groups with `uv add --dev` or the appropriate dependency group option for Ruff, `ty`, pytest, and any minimal test client support needed by the baseline tests.
- [x] 1.5 Configure Ruff, `ty`, pytest, and package discovery in `pyproject.toml`.
- [x] 1.6 Update `.gitignore` for Python caches, tool caches, build outputs, virtual environments, local environment files, and local databases while keeping `openspec/` and `.agents/` trackable.

## 2. Source Package Structure

- [x] 2.1 Create the `src/uniquode` package and baseline `__init__.py`.
- [x] 2.2 Create explicit package locations or modules for application construction, settings, route registration, models, migrations, and template conventions.
- [x] 2.3 Document or encode the selected Jinja2 template location without adding product-specific templates or static assets.

## 3. ASGI Application Shell

- [x] 3.1 Implement an application factory that returns a fresh FastAPI application instance.
- [x] 3.2 Expose a stable module-level ASGI app object at the selected import path.
- [x] 3.3 Add baseline route registration with async route handlers and no product-specific behavior.
- [x] 3.4 Ensure the application imports without requiring database state or product configuration.

## 4. Persistence Boundaries

- [x] 4.1 Add Tortoise ORM configuration boundaries for future PostgreSQL and SQLite use without introducing domain models.
- [x] 4.2 Add clear future locations for Tortoise models and migrations.
- [x] 4.3 Keep route handlers decoupled from direct database client construction or database access.

## 5. Validation Coverage

- [x] 5.1 Add tests that import the documented ASGI app path successfully.
- [x] 5.2 Add tests that construct the app through the application factory and verify baseline routes are registered.
- [x] 5.3 Add tests or inspections that verify baseline route handlers are async where they form request boundaries.
- [x] 5.4 Run and pass Ruff formatting, Ruff linting, `ty check src/`, and pytest through `uv run` project commands.

## 6. OpenSpec Verification

- [x] 6.1 Run `openspec validate init-project --strict` and resolve any artifact issues.
- [x] 6.2 Verify the implementation satisfies each `application-infrastructure` requirement and update this task list as work is completed.
