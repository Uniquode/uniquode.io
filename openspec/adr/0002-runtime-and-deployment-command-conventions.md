# 0002: Runtime and Deployment Command Conventions

Date: 2026-05-20

Status: Accepted

## Context

ADR 0001 selected FastAPI/Starlette, async-first ASGI, Python 3.13+, and `uv`
as the project manager and tool runner. The application exposes a stable ASGI
import path through host project metadata, currently `app.asgi:app`.

The project needs a repeatable way to run the application locally and a clear convention for deployment handoff. The command surface should keep using `uv run` so project-installed packages, `$PATH`, and `$VIRTUAL_ENV` are resolved by `uv`.

The runtime convention should not depend on a front-end build pipeline. The current application is a server-rendered or API-capable FastAPI application; front-end assets may be introduced later, but they are not required for the ASGI server to run.

## Decision

Use Uvicorn as the ASGI server for local and direct ASGI runtime execution.

The canonical ASGI target is configured by the host project's
`[tool.wybra].runserver_app` option. For this application, the target is:

```text
app.asgi:app
```

Wybra-owned operator commands should be exposed through prefixed package
scripts to avoid collisions with host application or environment-specific
commands. The ADR-owned command set is:

- `wybra-runserver`
- `wybra-migrate`
- `wybra-routes`
- `wybra-validate`
- `wybra-authmgr`

Package metadata, application docs, and specs should conform to this decision
without re-declaring those scripts from the host app package. The local
development server command is:

```text
wybra-runserver
```

The script should resolve the configured host ASGI target and start Uvicorn
against it. It should be run through `uv`:

```text
uv run wybra-runserver
```

For direct invocation in the current application, the equivalent command is:

```text
uv run uvicorn app.asgi:app
```

The `wybra-runserver` command uses the following baseline local defaults:

- host `127.0.0.1`;
- port `8000`;
- reload disabled by default.

The `wybra-runserver` command should support explicit local overrides for host
and port.

The `--reload` flag should enable reload explicitly. When `--reload` is not supplied, the `APP_RELOAD` environment variable may enable reload when set to a truthy value.

Production deployment must preserve ASGI handoff. If a process manager is
needed, use an ASGI-compatible deployment path, such as Gunicorn with a Uvicorn
worker or another deployment system that runs the same configured ASGI target.

## Consequences

The application can be run before any front-end pipeline exists because FastAPI is served directly through ASGI.

Developers get a prefixed package-owned command for local execution while the
underlying server target remains explicit and standard.

Using `uv run` keeps runtime behaviour tied to project metadata and the managed environment.

Keeping the ASGI target stable avoids coupling deployment configuration to internal application factory details.

If later requirements introduce a front-end build step, that step can be added
before or alongside `wybra-runserver` without changing the ASGI target.

## Follow-Up Work

No additional follow-up work is currently required by this ADR.
