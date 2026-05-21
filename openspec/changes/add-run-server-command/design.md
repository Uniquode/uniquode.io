## Context

ADR 0002 defines `uv run runserver` as the canonical local runtime command for the ASGI application at `uniquode.asgi:app`. The project already depends on Uvicorn and exposes the stable ASGI import path, but `pyproject.toml` does not yet provide the agreed script entry point or any validation around the runtime command contract.

This change touches the project's runtime surface rather than product behaviour. It should therefore remain small, avoid introducing any front-end or deployment-specific concerns, and preserve the existing FastAPI application structure.

## Goals / Non-Goals

**Goals:**

- Expose the canonical `runserver` command through project metadata.
- Keep the command aligned with ADR 0002 by targeting `uniquode.asgi:app`.
- Define predictable local defaults for host, port, and reload behaviour.
- Add focused validation that the runtime command wiring remains correct.
- Keep the change independent of any future front-end asset pipeline.

**Non-Goals:**

- Implement production deployment scripts or process manager configuration.
- Introduce environment-specific runtime configuration beyond the local baseline.
- Change the application factory or ASGI import contract.
- Add broader operational tooling such as container orchestration or service supervision.

## Decisions

### Use a `pyproject.toml` project script for `runserver`

The command should be exposed through project metadata so it is available consistently via `uv run runserver` without requiring developers to remember the full Uvicorn invocation.

Alternative considered:

- Document only `uv run uvicorn uniquode.asgi:app`
  - Rejected because ADR 0002 explicitly defines `runserver` as the stable local command surface.

### Keep the ASGI target fixed at `uniquode.asgi:app`

The script should invoke Uvicorn against the stable ASGI import path rather than importing the application factory directly or introducing another wrapper module. This keeps runtime and deployment configuration aligned with ADR 0002 and avoids coupling startup behaviour to internal application-construction details.

Alternatives considered:

- Point the script at an application factory import
  - Rejected because the accepted ADR already defines the stable target.
- Add a custom launcher module
  - Rejected because it adds indirection without solving a current requirement.

### Choose local-development defaults that favour interactive use

The `runserver` command should represent the normal local-development experience, so it should prefer localhost binding, the conventional development port, and reload enabled by default. These defaults make the command immediately useful while keeping the underlying Uvicorn invocation standard.

The launcher should parse supported command-line options and use the defaults only when an override is not supplied. This keeps the project-specific entry point flexible without exposing the whole Uvicorn configuration surface prematurely.

Alternatives considered:

- Disable reload by default
  - Rejected because the command is explicitly for local development and reload improves the default feedback loop.
- Bind to all interfaces by default
  - Rejected because localhost is the safer baseline unless a broader bind requirement emerges.
- Hard-code values with no command-line parsing
  - Rejected because the command would be unnecessarily rigid for local development and testing.

### Validate the runtime contract through focused startup coverage

This change should add small tests or smoke checks that prove the runtime wiring is present and points at the expected target, rather than attempting full end-to-end server process testing. The contract being introduced is primarily metadata and startup configuration, not request handling behaviour.

Alternatives considered:

- No test or validation coverage
  - Rejected because the change introduces a developer-facing runtime contract that could silently regress.
- Full subprocess-based server tests
  - Rejected because they add more complexity than the current scope justifies.

## Risks / Trade-offs

- [Reload defaults may behave differently across environments] -> Keep the contract focused on local development and leave production runtime behaviour to later deployment-specific work.
- [Project-script wiring can drift from ADR 0002 or from direct Uvicorn usage] -> Add focused validation around the configured command target and expected defaults.
- [Choosing defaults now may require later refinement] -> Keep host, port, and reload conventions simple and document them as the local baseline rather than as a permanent production contract.

## Migration Plan

1. Add the `runserver` project script to `pyproject.toml`.
2. Ensure the script invokes Uvicorn against `uniquode.asgi:app` with the agreed local defaults.
3. Add focused validation or smoke coverage for the runtime command contract.
4. Update any local documentation or implementation notes that describe how the application is run.

Rollback is straightforward: remove the script entry and the related validation if the approach proves unsuitable.

## Open Questions

- Whether the local baseline should use port `8000` explicitly or rely on the equivalent Uvicorn default while still documenting it.
- Whether runtime defaults should remain entirely in the script entry or be delegated to a small Python launcher if option growth later makes the script too opaque.
