## Why

Linear: [UT-225](https://linear.app/uniquode/issue/UT-225/add-migration-revision-command)

Module-owned migration locations are now part of the data infrastructure, but
the project migration CLI only applies and inspects existing revisions. Without
a project-supported revision command, developers must remember raw Alembic
options to place new files beside the owning module models and to express
cross-module graph dependencies correctly.

## What Changes

- Add a `wevra-migrate revision` command for creating Alembic revision files
  through the project migration wrapper.
- Require the owning configured module to be selected explicitly when creating
  a revision, so the generated file lands in that module's conventional
  `migrations/versions/` directory.
- Support the normal Alembic revision-generation controls needed for
  roll-forward work, including message, head, splice, branch label,
  dependency, revision id, and autogenerate options where they fit the current
  project infrastructure.
- Make command help and documentation explain the usual roll-forward order:
  update module models, create the owning module revision, review generated
  operations and graph pointers, run upgrade, then validate.
- Preserve existing `upgrade`, `downgrade`, `current`, `history`, database URL
  override, configured module discovery, and Alembic graph behaviour.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `development-database`: add a project-supported migration revision-generation
  workflow that places new revision files in the owning configured module and
  documents the normal roll-forward order.

## Impact

- Affected code includes `wevra.db.migrate`, Alembic configuration assembly,
  migration command tests, README migration documentation, and validation or
  helper tests for module-owned version locations.
- No new runtime dependency is expected; the implementation should continue
  using Click and Alembic already present in the project.
- The change affects developer workflow only. Existing databases and existing
  migration revision files are not rewritten.
