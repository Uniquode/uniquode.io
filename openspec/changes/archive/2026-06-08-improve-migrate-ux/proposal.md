## Why

Linear: [UT-224](https://linear.app/uniquode/issue/UT-224/improve-migrate-ux)

The `wevra-migrate` CLI currently follows Alembic's default model where an
empty database is implicitly at `base` and `wevra-migrate upgrade` can
initialise it as a side effect. Wevra should expose a stricter operational
lifecycle so first-time database provisioning, migration-state initialisation,
and routine schema upgrades are distinct and visible.

## What Changes

- Add a distinct `wevra-migrate init` command for first-time database
  provisioning and migration-state setup.
- Change `wevra-migrate upgrade` so it expects an already initialised managed
  database and fails with clear guidance when migration state is absent.
- Improve `wevra-migrate current` so it reports connection, initialisation, and
  current-revision state explicitly instead of relying on Alembic's silent
  "no current revision" behaviour.
- Model database lifecycle in backend-aware phases:
  - connection or availability;
  - database and principal provisioning where required;
  - Alembic migration-state initialisation;
  - ordinary migration upgrade or downgrade.
- Treat SQLite as a special case: a file-backed SQLite database may not require
  authentication or separate database creation, and `init` can create the file
  plus Alembic migration state without applying application schema revisions.
- Treat PostgreSQL and stricter managed databases as explicit provisioning
  environments: `init` provisions databases, users, roles, and permissions via
  a separate administrative connection before marking Alembic migration state.
- Use the existing `dbscripts` dependency as the provisioning mechanism for
  operations that cannot be performed through the ordinary application database
  connection.
- Keep ordinary application startup from creating databases, users, roles,
  permissions, migration state, or schema as an implicit side effect.
- Keep backend-specific diagnostics safe: command output should distinguish
  unavailable, unprovisioned, uninitialised, and current states without leaking
  credentials or raw driver traces.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `development-database`: Define explicit migration lifecycle UX for
  `wevra-migrate init`, backend-aware database provisioning, stricter
  `wevra-migrate upgrade`, and clearer `wevra-migrate current` state reporting.

## Impact

- Affected code is expected to include Wevra migration command infrastructure,
  database URL/backend inspection helpers, tests for SQLite and PostgreSQL-like
  lifecycle states, and application documentation for local development and
  stricter deployment environments.
- `wevra-migrate upgrade` behaviour will become stricter and may be a
  **BREAKING** change for workflows that currently rely on upgrade to
  initialise an empty database implicitly.
- The change should not add a runtime dependency; `dbscripts` is already
  declared by Wevra for out-of-band database provisioning support.
