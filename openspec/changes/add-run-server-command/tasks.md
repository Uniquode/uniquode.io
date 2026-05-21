## 1. Runtime command setup

- [x] 1.1 Add the `runserver` project script to `pyproject.toml` so `uv run runserver` starts `uniquode.asgi:app` with Uvicorn.
- [x] 1.2 Define and document the local-development defaults for host, port, and reload behaviour used by the `runserver` command.

## 2. Runtime contract validation

- [x] 2.1 Add focused test or smoke coverage that verifies the configured runtime command or its equivalent startup contract targets `uniquode.asgi:app`.
- [x] 2.2 Run the relevant validation commands to confirm the new runtime command wiring does not break the baseline application checks.

## 3. Developer workflow updates

- [x] 3.1 Update the relevant local documentation or implementation notes to describe the canonical `uv run runserver` workflow.
- [x] 3.2 Review the completed change against ADR 0002 and the `application-infrastructure` delta spec to confirm the runtime baseline is satisfied.
