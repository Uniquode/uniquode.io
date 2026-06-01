## ADDED Requirements

### Requirement: Runtime command Uvicorn pass-through
The system SHALL allow the `runserver` command to forward additional command-line
arguments to Uvicorn after a `--` separator while preserving the project-owned
ASGI target and local runtime defaults.

#### Scenario: Uvicorn arguments are forwarded
- **WHEN** a developer runs `uv run runserver -- --forwarded-allow-ips 127.0.0.1`
- **THEN** the command invokes Uvicorn for `uniquode.asgi:app` with
  `--forwarded-allow-ips 127.0.0.1`

#### Scenario: Project runtime options still apply
- **WHEN** a developer runs `uv run runserver --host 0.0.0.0 --port 9000 -- --proxy-headers`
- **THEN** the command applies the project `--host` and `--port` options and
  passes `--proxy-headers` through to Uvicorn

#### Scenario: Application target remains project-owned
- **WHEN** a developer runs `uv run runserver -- other.asgi:app`
- **THEN** the command rejects the extra application target instead of passing
  two positional application targets to Uvicorn

#### Scenario: Reload environment fallback remains available
- **WHEN** a developer runs `uv run runserver -- <uvicorn args>` without the
  project `--reload` option and `APP_RELOAD` is set to a truthy value
- **THEN** the command starts Uvicorn with reload enabled and preserves the
  supplied Uvicorn arguments

#### Scenario: Reload environment fallback can be disabled explicitly
- **WHEN** a developer runs `uv run runserver --no-reload` and `APP_RELOAD` is
  set to a truthy value
- **THEN** the command starts Uvicorn without reload enabled

### Requirement: Project CLI parser standard
The system SHALL use Click for project-owned command-line entrypoints covered by
this change while preserving their documented command interfaces.

#### Scenario: Click dependency is direct
- **WHEN** project CLI code imports Click
- **THEN** `pyproject.toml` lists Click as a direct runtime dependency

#### Scenario: Validation command keeps existing behaviour
- **WHEN** a developer runs the validation command with existing targets,
  verbosity, or override options
- **THEN** the command accepts the same options and reports the same validation
  outcomes and exit status as before the parser migration

## MODIFIED Requirements

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
