## 1. Migration Lifecycle Inspection

- [x] 1.1 Add tests for reachable uninitialised SQLite databases, missing SQLite
  database files, and unavailable PostgreSQL-like connection failures.
- [x] 1.2 Add shared migration state inspection that distinguishes unavailable,
  uninitialised, and initialised migration states without leaking credentials.
- [x] 1.3 Make `wevra-migrate current` report explicit migration state for
  uninitialised databases while preserving current-revision reporting.

## 2. Initialisation And Upgrade Semantics

- [x] 2.1 Add `wevra-migrate init` tests for first-time SQLite migration-state
  initialisation, no schema migration, and existing database URL override
  behaviour.
- [x] 2.2 Implement `wevra-migrate init` as the explicit first-time
  provisioning and Alembic base-state command without applying application
  revisions.
- [x] 2.3 Add failing tests that prove `wevra-migrate upgrade` rejects databases
  with no Alembic migration state.
- [x] 2.4 Add the pre-upgrade migration-state check and clear remediation
  message pointing first-time setup to `wevra-migrate init`.
- [x] 2.5 Update auth-management schema remediation text to reference
  `wevra-migrate init` when the configured database is not initialised.
- [x] 2.6 Add PostgreSQL init tests for admin URL provisioning delegation,
  missing admin URL diagnostics, and no application revision upgrade.
- [x] 2.7 Implement PostgreSQL provisioning in `wevra-migrate init` through
  dbscripts while keeping application startup and `upgrade` non-provisioning.

## 3. Revision Command Integration

- [x] 3.1 Complete the `add-migration-revision-command` implementation tasks in
  the same Wevra branch, sharing migration configuration and database URL
  handling with the lifecycle commands.
- [x] 3.2 Ensure `revision`, `init`, `upgrade`, `current`, `history`, and
  `downgrade` keep one consistent Click root and error-reporting style.

## 4. Documentation And Host App Follow-Up

- [x] 4.1 Update Wevra README migration documentation for `init`, strict
  `upgrade`, explicit current-state reporting, and revision generation.
- [x] 4.2 Update host app tests/docs that currently assume `upgrade`
  initialises an empty SQLite database.
- [x] 4.3 Run focused migration command tests in Wevra and the host app.
- [x] 4.4 Run standard Wevra and host app lint, formatting, type, test, and
  OpenSpec validation checks.
