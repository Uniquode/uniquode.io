## Why

Several project CLIs currently use small argparse wrappers, while Uvicorn
already uses Click and `runserver` needs clean pass-through support for
deployment-specific Uvicorn options. Moving project-owned CLIs to Click gives us
a clearer command model, makes `runserver -- <uvicorn args>` practical, and
keeps CLI behaviour consistent as commands grow.

## What Changes

- Add Click as an explicit runtime dependency rather than relying on Uvicorn's
  transitive dependency.
- Change `runserver` parsing from argparse to Click while preserving current
  defaults for host, port, and reload.
- Allow `runserver` to forward additional command-line arguments after `--` to
  Uvicorn, for example proxy-header trust options needed behind Nginx.
- Change the `validate` CLI from argparse to Click while preserving targets,
  verbosity, override options, output, and exit codes.
- Change the `migrate` CLI from argparse to Click while preserving migration
  subcommands, revision arguments, database URL override behaviour, and exit
  codes.
- Change the `usermgr` CLI from argparse to Click for consistency and cleaner
  command/subcommand handling while preserving its existing operator interface.
- Preserve existing environment-backed behaviour such as `APP_RELOAD` unless a
  later design decision explicitly changes it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `application-infrastructure`: `runserver` command parsing changes to Click
  and supports pass-through Uvicorn arguments after `--`; `validate` command
  parsing changes to Click without changing validation behaviour.
- `development-database`: `migrate` command parsing changes to Click without
  changing Alembic command behaviour or database URL override semantics.
- `user-management-cli`: `usermgr` command parsing changes to Click without
  changing command names, flags, password-source semantics, outputs, or exit
  codes.

## Impact

- Affects `src/uniquode/runserver.py`, `src/uniquode/validate.py`,
  `src/uniquode/migrate.py`, `src/auth_ext/usermgr.py`, related tests, and CLI
  documentation.
- Adds `click` as a direct runtime dependency in project metadata and lockfile.
