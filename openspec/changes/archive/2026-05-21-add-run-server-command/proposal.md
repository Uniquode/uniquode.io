## Why

The project has a stable ASGI application target, but it still lacks the agreed local runtime command defined by ADR 0002. Adding the `runserver` command now makes local execution predictable before the next web-foundation and UI work begins.

## What Changes

- Add the project-defined `runserver` command so the application can be started consistently through `uv run runserver`.
- Define the expected runtime behaviour for the local server command, including its ASGI target and baseline host, port, and reload conventions.
- Add focused validation or smoke coverage for the runtime command where practical.
- Document the runtime command as part of the project's established infrastructure workflow.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `application-infrastructure`: Extend the infrastructure requirements to cover the standard local runtime command, its expected ASGI target, and the baseline validation of application startup.

## Impact

- `pyproject.toml` project script configuration
- ASGI runtime dependencies and command wiring
- Runtime and developer workflow documentation
- Focused tests or startup validation for the application entry point
