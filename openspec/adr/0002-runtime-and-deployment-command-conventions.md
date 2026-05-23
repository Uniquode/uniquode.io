# 0002: Runtime and Deployment Command Conventions

Date: 2026-05-20

Status: Accepted

## Context

ADR 0001 selected FastAPI/Starlette, async-first ASGI, Python 3.14, and `uv` as the project manager and tool runner. The initial application now exposes a stable ASGI import path at `uniquode.asgi:app`.

The project needs a repeatable way to run the application locally and a clear convention for deployment handoff. The command surface should keep using `uv run` so project-installed packages, `$PATH`, and `$VIRTUAL_ENV` are resolved by `uv`.

The runtime convention should not depend on a front-end build pipeline. The current application is a server-rendered or API-capable FastAPI application; front-end assets may be introduced later, but they are not required for the ASGI server to run.

## Decision

Use Uvicorn as the ASGI server for local and direct ASGI runtime execution.

The canonical ASGI target is:

```text
uniquode.asgi:app
```

The local development server command should be exposed through a project script named:

```text
runserver
```

The script should start Uvicorn against `uniquode.asgi:app`. It should be run through `uv`:

```text
uv run runserver
```

For direct invocation, the equivalent command is:

```text
uv run uvicorn uniquode.asgi:app
```

The `runserver` command uses the following baseline local defaults:

- host `127.0.0.1`;
- port `8000`;
- reload disabled by default.

The `runserver` command should support explicit local overrides for host and port.

The `--reload` flag should enable reload explicitly. When `--reload` is not supplied, the `U_RELOAD` environment variable may enable reload when set to a truthy value.

Production deployment must preserve ASGI handoff. If a process manager is needed, use an ASGI-compatible deployment path, such as Gunicorn with a Uvicorn worker or another deployment system that runs the same `uniquode.asgi:app` target.

## Consequences

The application can be run before any front-end pipeline exists because FastAPI is served directly through ASGI.

Developers get a short project-specific command for local execution while the underlying server target remains explicit and standard.

Using `uv run` keeps runtime behaviour tied to project metadata and the managed environment.

Keeping the ASGI target stable avoids coupling deployment configuration to internal application factory details.

If later requirements introduce a front-end build step, that step can be added before or alongside `runserver` without changing the ASGI target.

## Follow-Up Work

No additional follow-up work is currently required by this ADR.
