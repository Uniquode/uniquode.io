## Why

The project needs an initial application infrastructure that turns the accepted platform decisions into a concrete, repeatable Python project layout. This should establish the foundation for the web application without introducing product dependencies before requirements need them.

## External Tracking

- Linear: `UT-5`

## What Changes

- Initialize the project as a Python 3.14 application managed by `uv`.
- Create project metadata using `pyproject.toml` with `uv_build` as the build backend.
- Establish a `src/` layout with `src/uniquode` as the main package.
- Define the initial package structure for settings, URL or route mappings, basic application models, and migrations.
- Establish the FastAPI/Starlette ASGI application entrypoint and keep the app async-first.
- Define conventions for checks using Ruff formatting, Ruff linting, `ty`, and pytest.
- Define where templates will live when server-rendered UI work begins, while avoiding template implementation before a concrete requirement exists.
- Keep runtime dependencies limited to the platform needs already accepted in ADR 0001; add further dependencies only when requirements justify them.

## Capabilities

### New Capabilities

- `application-infrastructure`: Project initialization, source layout, Python package structure, ASGI application shell, configuration boundaries, check commands, and dependency discipline for the initial FastAPI application.

### Modified Capabilities

None.

## Impact

- Adds or updates Python project metadata and build configuration.
- Creates the initial `src/uniquode` package structure.
- Establishes initial locations for settings, routing, models, migrations, tests, and future templates.
- Adds the baseline development tool configuration for `uv`, Ruff, `ty`, and pytest.
- Does not implement product features, database-backed domain models, or front-end templates beyond infrastructure conventions.
