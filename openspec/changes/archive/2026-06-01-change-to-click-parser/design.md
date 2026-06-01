## Context

`runserver` is a project-owned wrapper around Uvicorn that fixes the stable ASGI
target and supplies development-oriented defaults. Recent session-cookie work
made trusted forwarded proxy headers operationally important: when Nginx
terminates TLS and connects to the app over HTTP, Uvicorn must be configured to
trust the proxy before the ASGI request scheme can correctly represent the
external HTTPS request.

The current `runserver` argparse wrapper handles only project-owned flags and
calls `uvicorn.run(...)` directly. That is sufficient for local development, but
it does not scale well for pass-through Uvicorn options without reimplementing
Uvicorn's CLI surface. `validate`, `migrate`, and `usermgr` are also
project-owned argparse CLIs. `usermgr` has the largest compatibility surface,
but its command/subcommand shape is a good match for Click once password-source
semantics are preserved explicitly.

## Goals / Non-Goals

**Goals:**

- Make `runserver -- <uvicorn args>` an explicit supported command shape.
- Use Click as a direct project dependency for project-owned CLI parsing rather
  than relying on a transitive dependency.
- Preserve `runserver` defaults for ASGI target, host, port, and reload.
- Preserve `APP_RELOAD` fallback behaviour when `--reload` is not supplied.
- Delegate additional Uvicorn options to Uvicorn's own CLI parsing, including
  proxy-header trust options such as `--forwarded-allow-ips`.
- Convert `validate`, `migrate`, and `usermgr` to Click while preserving their
  existing command-line interfaces and return behaviour.
- Use Click's built-in hidden password prompt for interactive `usermgr`
  password entry while keeping the stricter one-line non-TTY stdin contract for
  `--password -`.

**Non-Goals:**

- Reimplement Uvicorn's CLI option parser.
- Add first-class project options for every Uvicorn setting.
- Change the stable ASGI app import path.
- Change validation targets, migration semantics, Alembic integration, or
  user management semantics.
- Add a new production process manager or deployment system.

## Decisions

### Use Click directly for project CLI parsing

Use Click as an explicit runtime dependency and parser for project-owned CLIs
covered by this change. This is preferable to continuing to stretch argparse
because Click supports unprocessed trailing arguments directly, models
subcommands cleanly, and matches Uvicorn's existing CLI stack.

Alternative considered: keep argparse with `argparse.REMAINDER`. That works for
basic pass-through but gives a less natural command model and does not move the
project towards a consistent command/subcommand parser for richer CLIs.

### Keep `runserver` as the project-owned command boundary

`runserver` should continue to own the application target and baseline defaults:
`uniquode.asgi:app`, `127.0.0.1`, port `8000`, and reload controlled by
`--reload` or `APP_RELOAD`. Additional Uvicorn arguments are appended after
those defaults when invoking Uvicorn.

Alternative considered: tell operators to call `uvicorn uniquode.asgi:app`
directly. That would remove duplicated wrapper logic but would also bypass the
documented project command and require operators to remember the app target and
project conventions.

### Delegate Uvicorn-specific options to Uvicorn

Arguments after `--` should be passed to Uvicorn's CLI entrypoint rather than
translated into `uvicorn.run(...)` keyword arguments by our wrapper. This keeps
Uvicorn-specific parsing, validation, defaults, and future options with Uvicorn.

Alternative considered: inspect and map Uvicorn options into `uvicorn.run(...)`
keyword arguments. That would be brittle and would need ongoing maintenance as
Uvicorn changes.

### Convert `validate` and `migrate` as low-risk parser migrations

`validate` and `migrate` should move to Click in this change because both are
small project-owned CLIs and their argparse usage maps directly to Click
options, arguments, and groups. The implementation should preserve their public
command shape:

- `validate [--verbose] [--template-root ...] [--static-root ...]
  [--static-url-path ...] [--database-url ...] [--migrations-root ...]
  [--alembic-config ...] [targets...]`
- `migrate [--database-url ...] upgrade [revision]`
- `migrate [--database-url ...] downgrade <revision>`
- `migrate [--database-url ...] current`
- `migrate [--database-url ...] history`

Alternative considered: leave `validate` and `migrate` on argparse until the
`runserver` pass-through is implemented. That would reduce immediate files
touched, but it would miss an inexpensive chance to make the core project CLIs
consistent while the Click dependency is being introduced.

### Convert `usermgr` as part of the parser migration

`usermgr` should move to Click in this change for consistency with the other
project-owned CLIs. The migration must preserve current command names, flags,
password source handling, output modes, and exit behaviour. Parser-focused tests
should use Click's `CliRunner` rather than fabricated parser simulations.

Interactive password entry should use Click's hidden prompt and confirmation
loop. The `--password -` path remains application-owned because Click does not
provide the exact policy required here: reject interactive TTY stdin, reject
empty stdin, preserve password whitespace except the trailing newline, and reject
extra data after the first line.

Alternative considered: leave `usermgr` on argparse for a later change. That
would reduce this diff, but it would keep the most command-heavy local operator
CLI on the old parser immediately after adopting Click as the project parser
standard.

## Risks / Trade-offs

- Click becomes a direct runtime dependency. -> Add it through `uv add` so
  project metadata and the lockfile make the dependency explicit.
- Delegating to Uvicorn's CLI may raise Click `SystemExit` paths rather than
  returning like `uvicorn.run(...)`. -> Keep `runserver` as a process entrypoint
  and cover argument construction/delegation in tests.
- Parser migrations can accidentally change exit codes or error output. -> Keep
  existing CLI tests focused on externally visible command results rather than
  Click internals.
- Pass-through options can override project defaults if Uvicorn accepts repeated
  flags with last-value-wins behaviour. -> Document that arguments after `--`
  are Uvicorn-owned escape hatches for advanced operation.
- Incorrect proxy trust configuration can allow spoofed forwarded scheme
  headers. -> Document trusted proxy IP configuration and avoid defaulting to
  unrestricted `*`.
