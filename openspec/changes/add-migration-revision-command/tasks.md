## 1. Revision Placement Helpers

- [ ] 1.1 Add a `wevra.db` helper that resolves a configured module's
  conventional `migrations/versions/` path from the module package location.
- [ ] 1.2 Ensure the helper rejects missing or unconfigured modules clearly
  before revision generation attempts to write files.
- [ ] 1.3 Ensure Alembic config assembly can include the selected module's
  target version location even when that directory does not exist yet.

## 2. Migration CLI

- [ ] 2.1 Add `migrate revision` as a Click subcommand under `wevra.db.migrate`.
- [ ] 2.2 Require `--module <module>` and `-m/--message` for revision creation.
- [ ] 2.3 Pass `--autogenerate`, `--head`, `--splice`, `--branch-label`,
  `--depends-on`, and `--rev-id` through to Alembic revision generation.
- [ ] 2.4 Preserve existing `upgrade`, `downgrade`, `current`, `history`, and
  database URL override behaviours.
- [ ] 2.5 Make `migrate revision --help` explain the usual roll-forward order
  and clarify that Alembic graph pointers control ordering.

## 3. Tests

- [ ] 3.1 Add tests proving `revision` passes the selected module's
  conventional `version_path` to Alembic.
- [ ] 3.2 Add tests proving missing `--module` and unconfigured module inputs
  fail without creating revision files.
- [ ] 3.3 Add tests proving first-revision module locations are accepted by the
  generated Alembic configuration.
- [ ] 3.4 Add tests proving autogenerate and graph options are passed through
  while file placement remains module-owned.
- [ ] 3.5 Add tests proving existing migration subcommands and database URL
  override behaviour are unchanged.
- [ ] 3.6 Add tests proving `migrate revision --help` includes the documented
  roll-forward order.

## 4. Documentation And Validation

- [ ] 4.1 Update README migration documentation with the module-owned revision
  command and roll-forward sequence.
- [ ] 4.2 Update any validation or help-text expectations that list migration
  command capabilities.
- [ ] 4.3 Run focused migration command tests.
- [ ] 4.4 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest -q`,
  `uv run validate --verbose`, and
  `uv run openspec validate add-migration-revision-command --strict`.
