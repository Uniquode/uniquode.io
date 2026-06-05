## Context

The project now composes data infrastructure from configured modules. Existing
migration application already discovers configured module version locations and
Alembic applies revisions according to the graph declared by `revision`,
`down_revision`, and `depends_on`.

The remaining gap is revision creation. `data_core.migrate` currently exposes
`upgrade`, `downgrade`, `current`, and `history`, but not Alembic's revision
generation operation. With multiple module-owned version locations, raw
Alembic generation requires developers to remember the correct `version_path`
for the owning module. That is easy to get wrong, especially when a new module
revision depends on another module's head.

## Goals / Non-Goals

**Goals:**

- Add a project-supported `migrate revision` command that creates new Alembic
  revision files in the owning configured module.
- Keep module ownership explicit by requiring a module name for revision
  creation.
- Preserve Alembic's graph model: ordering is expressed with `down_revision`
  and `depends_on`, not by module order or filename.
- Support the common roll-forward workflow in command help and documentation:
  ensure the database is at the previous head, update models, generate the
  owning module revision, review generated operations and graph pointers, run
  upgrade, then validate.
- Keep existing apply/status migration commands unchanged.

**Non-Goals:**

- Do not invent a custom migration graph format.
- Do not infer cross-module revision dependencies from ORM foreign keys.
- Do not rewrite or relocate existing migration revisions.
- Do not add a general migration linter or automatic schema-review system.
- Do not introduce new runtime dependencies.

## Decisions

### Require `--module` For Revision Placement

`migrate revision` should require an owning configured module:

```text
uv run migrate revision --module auth_ext -m "add identity table"
```

The command resolves the module's conventional version directory from the
module package location:

```text
<module>/migrations/versions/
```

If the directory does not exist yet, revision generation may create it. The
module itself must be importable and present in the active composition
configuration. Installed but unconfigured modules should not receive migration
files through this project command.

Alternative considered: infer placement from the selected Alembic head. That
matches one Alembic behaviour when multiple version locations exist, but it
conflates graph order with schema ownership. A `uniquode` revision that depends
on an `auth_ext` revision should still live under `uniquode` when it changes
`uniquode` tables.

### Delegate Revision Generation To Alembic

The command should call `alembic.command.revision()` with the project Alembic
configuration, setting `version_path` to the resolved module version directory.
The command should expose Alembic controls that developers need to express
ordinary graph relationships:

- `-m` / `--message`
- `--autogenerate`
- `--head`
- `--splice`
- `--branch-label`
- `--depends-on`
- `--rev-id`

`--head` should default to Alembic's `head`, matching Alembic's normal
behaviour. `--depends-on` should be documented as the explicit way to express
cross-module dependency when the new revision belongs to a different branch but
requires another module's revision to exist.

Alternative considered: provide a narrow `--autogenerate`-only wrapper. That
would be simpler, but it would force developers back to raw Alembic whenever a
branch label, explicit head, splice, dependency, or deterministic revision id is
needed.

### Keep Version Locations Composed

The same `build_alembic_config()` path should continue to set discovered module
`version_locations`. For revision creation, the selected module's target
version directory should be included in the config even when this is the first
revision for that module. Alembic validates that `version_path` is one of the
configured locations before writing the file.

Alternative considered: bypass Alembic's version-location validation and write
the file directly. That would duplicate Alembic behaviour and increase the
chance that generated files diverge from the configured migration environment.

### Make Roll-Forward Order Visible In CLI Help

The `revision` command help should state the usual safe sequence:

1. Ensure the working database is upgraded to the current head.
2. Update the owning module's models.
3. Run `migrate revision --module <module> --autogenerate -m "..."`
   or create an empty revision when hand-authored changes are needed.
4. Review generated operations plus `down_revision` / `depends_on`.
5. Run `migrate upgrade`.
6. Run validation.

This belongs in command help because it is a developer workflow concern that
will otherwise be easy to misremember.

## Risks / Trade-offs

- [Risk] Autogenerate can produce misleading output when the developer database
  is not at the previous head. -> Mitigation: document and test command help
  that instructs developers to upgrade first in the ordinary roll-forward path.
- [Risk] Developers may expect module order to imply revision order. ->
  Mitigation: documentation should state that module order controls discovery,
  while Alembic revision metadata controls ordering.
- [Risk] A newly created module migration directory may not be included in
  package builds if package data configuration changes later. -> Mitigation:
  keep tests or build checks covering bundled module migration files.
- [Risk] Multiple heads can be created accidentally when `--splice` or
  explicit heads are used incorrectly. -> Mitigation: preserve Alembic's own
  errors and expose graph controls without hiding their semantics.

## Migration Plan

This change affects developer tooling only. Existing databases, revision ids,
and revision files do not need migration.

Implementation should add tests before changing the command path, then update
documentation and run the focused migration command tests plus the standard
Ruff, type, pytest, validation, and OpenSpec checks.

## Open Questions

- None.
