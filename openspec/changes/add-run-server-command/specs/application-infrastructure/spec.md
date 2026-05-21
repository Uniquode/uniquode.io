## ADDED Requirements

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
- **WHEN** a developer runs `uv run runserver` without `--reload` and `U_RELOAD` is set to a truthy value
- **THEN** the application starts with reload enabled

#### Scenario: Runtime contract stays independent of front-end tooling
- **WHEN** the local runtime command is reviewed
- **THEN** it does not require a front-end asset pipeline in order to start the ASGI application

### Requirement: Runtime command validation
The system SHALL provide focused validation that the local runtime command wiring remains aligned with the documented ASGI target and startup contract.

#### Scenario: Runtime command wiring is covered
- **WHEN** the project's validation checks are run
- **THEN** at least one focused test or smoke check verifies the configured local runtime command or its equivalent startup contract
