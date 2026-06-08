## 1. Package Boundary

- [x] 1.1 Inventory current direct imports from `wevra.auth.cli.identitymgr`
  in tests and project code, plus shared CLI/database helpers used by
  `wevra-authmgr`, `wevra-migrate`, and other Wevra project commands.
- [x] 1.2 Create the `src/wevra/auth/cli/authmgr/` package structure with
  `__init__.py` exporting the supported public CLI surface.
- [x] 1.3 Move the current CLI module into the package without changing runtime
  behaviour, and update `wevra-authmgr` to resolve to
  `wevra.auth.cli.authmgr:main`.
- [x] 1.4 Remove the old single-file module once package import and script
  metadata are confirmed.

## 2. Shared Modules And Cross-Command Helpers

- [x] 2.1 Move command argument dataclasses and shared constants into a focused
  package module.
- [x] 2.2 Move password-source and timestamp parsing helpers into focused auth
  manager modules.
- [x] 2.3 Move schema preflight helpers into a focused schema module.
- [x] 2.4 Move output formatting helpers into a focused output module.
- [x] 2.5 Keep shared modules independent of resource command registration
  modules to avoid circular imports.
- [x] 2.6 Move concrete cross-command database, configuration, session, or
  diagnostic helpers into shared Wevra tooling modules instead of auth-specific
  modules when another Wevra CLI uses the same concern.
- [x] 2.7 Keep auth-specific helpers inside the auth manager package unless a
  second current command needs the same helper.

## 3. Command Registration

- [x] 3.1 Implement root CLI construction in a package module that owns
  `authmgr_command` and `main`.
- [x] 3.2 Add explicit `register_user_commands(root_command)` registration for
  user operations.
- [x] 3.3 Add explicit `register_scope_commands(root_command)` registration for
  scope operations.
- [x] 3.4 Add explicit `register_group_commands(root_command)` registration for
  group operations while preserving the existing target-first parser.
- [x] 3.5 Keep dispatcher command identifiers and service dispatch behaviour
  unchanged.
- [x] 3.6 Ensure registration is explicit and does not scan packages, entry
  points, filesystem paths, or plugin registries.

## 4. Behaviour Preservation Tests

- [x] 4.1 Add or update tests that confirm `wevra-authmgr` resolves to
  `wevra.auth.cli.authmgr:main`.
- [x] 4.2 Add or update tests that confirm `wevra.auth.cli.authmgr` exports the
  supported public CLI surface after the package split.
- [x] 4.3 Add or update tests that confirm root, user, group, and scope command
  help output remains stable.
- [x] 4.4 Run the focused auth-management CLI test suite during the split and
  keep existing user, group, scope, membership, output, password-source, and
  schema-preflight coverage passing.
- [x] 4.5 Add a test or inspection that fails if command composition relies on
  automatic package or entry-point discovery.
- [x] 4.6 Add or update tests proving shared database/configuration helpers used
  by `wevra-authmgr` remain aligned with the corresponding project command
  path rather than duplicating auth-private logic.

## 5. Verification

- [x] 5.1 Run Ruff formatting and linting checks for touched files.
- [x] 5.2 Run type checking for `src/`.
- [x] 5.3 Run the full test suite.
- [x] 5.4 Validate `modularise-auth-management-cli` with OpenSpec strict mode.
