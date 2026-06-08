## Context

`wevra-migrate` currently delegates directly to Alembic operations. That makes
routine migration application work, but it also inherits Alembic's implicit
empty-database model: an uninitialised SQLite file is treated as being at
`base`, and `upgrade` can create the database schema as a side effect.

The desired operational model is stricter. Database and principal provisioning,
Alembic state initialisation, and ordinary schema upgrades are separate
lifecycle steps. SQLite remains a special case because opening a file-backed
SQLite database can create the file and has no authentication boundary. More
strict backends such as PostgreSQL require explicit provisioning through
separate administrative credentials before the application connection can own
schema migration work.

This change is related to `add-migration-revision-command`: both extend the
same `wevra-migrate` command tree and both need the effective migration
configuration to be constructed consistently.

## Goals / Non-Goals

**Goals:**

- Add `wevra-migrate init` as the explicit first-time provisioning and
  migration-state initialisation command.
- Ensure `wevra-migrate init` does not apply application schema revisions; it
  stops after provisioning and Alembic base-state initialisation.
- Make `wevra-migrate upgrade` fail clearly when Alembic migration state is
  absent instead of silently initialising the database.
- Make `wevra-migrate current` report whether the configured database is
  unavailable, uninitialised, or at a current revision.
- Keep diagnostics backend-aware and safe by avoiding credential leakage and raw
  driver traces in expected failure output.
- Preserve existing database URL override behaviour and configured-module
  migration composition.
- Implement the migration lifecycle UX and revision-generation command through
  shared migration command helpers where they overlap.

**Non-Goals:**

- Apply application schema revisions during `wevra-migrate init`.
- Create PostgreSQL databases, roles, users, or privileges during ordinary
  application startup or routine `wevra-migrate upgrade`.
- Replace dbscripts as the PostgreSQL provisioning mechanism.
- Add a new runtime dependency.
- Change Alembic's revision graph semantics.
- Add automatic schema validation beyond the explicit command checks described
  here.

## Decisions

### Add `init` As The Provisioning And State Boundary

`wevra-migrate init` owns first-time database readiness and Alembic state
creation, but not application schema migration. For SQLite, this command may
create the database file and Alembic version table. For PostgreSQL-like
backends, it provisions the database, user, role, and privileges through
dbscripts and an administrative connection, then connects as the application
principal to initialise Alembic state at `base`.

Alternative considered: keep `upgrade` as both initialisation and upgrade. That
is convenient for local SQLite but hides whether the operator is creating a
database for the first time or applying a routine schema update.

Alternative considered: make `init` run all migrations after provisioning. That
recreates the old implicit `upgrade` behaviour under a different command name
and makes the `init` boundary too broad.

### Make `upgrade` Require Existing Alembic State

Before invoking Alembic `upgrade`, the command inspects the configured database
for the Alembic version table. If migration state is absent, `upgrade` fails
with guidance to run `wevra-migrate init` first. After `init` has created
Alembic base state, `upgrade` is responsible for applying application schema
revisions.

Alternative considered: check for every expected model table before upgrade.
That would turn the command into a broader schema validator and could make
legitimate partial states harder to recover. The Alembic version table is the
right boundary for whether the database is migration-managed.

### Keep Backend Handling In Inspection Helpers

Connection and state inspection should live in `wevra.db` migration helpers so
`init`, `upgrade`, and `current` report states consistently. SQLite path
detection should only apply when the database URL is SQLite; PostgreSQL and
other strict backends should rely on connection attempts and SQLAlchemy errors.

Alternative considered: parse every backend URL and predict availability before
connecting. SQLAlchemy already owns backend connection behaviour, and
pre-connection parsing would be incomplete for managed deployments.

### Provision PostgreSQL Explicitly During Init

Provisioning databases, users, roles, and permissions remains outside ordinary
application startup and outside `wevra-migrate upgrade`, but it is part of
`wevra-migrate init` for PostgreSQL. The command uses the existing `dbscripts`
dependency and requires an administrative PostgreSQL connection, supplied
explicitly or through the existing `SA_DATABASE_URL` dbscripts convention.

Alternative considered: keep PostgreSQL provisioning fully external to
`wevra-migrate`. That leaves `init` unable to perform the first-time lifecycle
step that PostgreSQL actually needs and forces operators to remember a second
tool before Wevra can initialise migration state.

### Share Configuration For Revision Generation

`init`, `upgrade`, `current`, `history`, and `revision` should all use the same
settings loader, database URL override handling, module composition, and
Alembic configuration builder. The revision-generation command may add a target
module version location, but it should not create a parallel configuration
path.

Alternative considered: implement revision generation in a separate command
module with its own settings setup. That would duplicate the exact configuration
logic this change is making more explicit.

## Risks / Trade-offs

- [Risk] Existing local workflows that use `wevra-migrate upgrade` on an empty
  SQLite database will fail. -> Mitigation: provide a clear error that points
  to `wevra-migrate init`, and document the required `init` then `upgrade`
  sequence.
- [Risk] PostgreSQL init requires administrative credentials. -> Mitigation:
  accept an explicit admin database URL and fall back to dbscripts'
  `SA_DATABASE_URL` convention while redacting credentials from diagnostics.
- [Risk] SQLite file checks can accidentally assume too much about URL shape. ->
  Mitigation: only apply SQLite path-specific messaging after the existing
  SQLite URL parser recognises the URL.
- [Risk] `init` and `revision` could diverge from ordinary migration config. ->
  Mitigation: keep a single Alembic config builder and test shared database URL
  override/module behaviour across commands.

## Migration Plan

1. Add focused tests for migration lifecycle state reporting, provisioning
   `init`, strict `upgrade`, and revision creation before changing command
   behaviour.
2. Implement shared migration state inspection, PostgreSQL provisioning, and
   command dispatch changes in Wevra.
3. Update app-level tests and documentation to use `wevra-migrate init`
   followed by `wevra-migrate upgrade` for first-time SQLite schema setup.
4. Run Wevra checks first, merge the Wevra PR, then verify the host app against
   the merged Wevra `main`.

Rollback is straightforward: remove `init` and the pre-upgrade state check to
return to Alembic's implicit empty-database behaviour.

## Open Questions

- None.
