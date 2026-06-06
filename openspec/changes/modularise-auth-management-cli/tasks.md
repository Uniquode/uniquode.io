## 1. Package Boundary

- [ ] 1.1 Inventory current direct imports from `wevra.auth.cli.identitymgr` in tests
  and project code.
- [ ] 1.2 Create the `src/wevra/auth/cli/identitymgr/` package structure with
  `__init__.py` exporting `main` and intentionally supported helper names.
- [ ] 1.3 Move the current CLI module into the package without changing runtime
  behaviour, keeping `identitymgr = "wevra.auth.cli.identitymgr:main"` working.
- [ ] 1.4 Remove the old single-file module once package import compatibility is
  confirmed.

## 2. Shared Modules

- [ ] 2.1 Move command argument dataclasses and shared constants into a focused
  package module.
- [ ] 2.2 Move password-source and timestamp parsing helpers into focused shared
  modules.
- [ ] 2.3 Move schema preflight helpers into a focused schema module.
- [ ] 2.4 Move output formatting helpers into a focused output module.
- [ ] 2.5 Keep shared modules independent of resource command registration
  modules to avoid circular imports.

## 3. Command Registration

- [ ] 3.1 Implement root CLI construction in a package module that owns
  `identitymgr_command` and `main`.
- [ ] 3.2 Add explicit `register_user_commands(root_command)` registration for
  user operations.
- [ ] 3.3 Add explicit `register_scope_commands(root_command)` registration for
  scope operations.
- [ ] 3.4 Add explicit `register_group_commands(root_command)` registration for
  group operations while preserving the existing target-first parser.
- [ ] 3.5 Keep dispatcher command identifiers and service dispatch behaviour
  unchanged.
- [ ] 3.6 Ensure registration is explicit and does not scan packages, entry
  points, filesystem paths, or plugin registries.

## 4. Behaviour Preservation Tests

- [ ] 4.1 Add or update tests that confirm `wevra.auth.cli.identitymgr:main` remains
  the project script entry point.
- [ ] 4.2 Add or update tests that confirm `wevra.auth.cli.identitymgr` exports
  `main` and required helper names after the package split.
- [ ] 4.3 Add or update tests that confirm root, user, group, and scope command
  help output remains stable.
- [ ] 4.4 Run the focused auth-management CLI test suite during the split and
  keep existing user, group, scope, membership, output, password-source, and
  schema-preflight coverage passing.
- [ ] 4.5 Add a test or inspection that fails if command composition relies on
  automatic package or entry-point discovery.

## 5. Verification

- [ ] 5.1 Run Ruff formatting and linting checks for touched files.
- [ ] 5.2 Run type checking for `src/`.
- [ ] 5.3 Run the full test suite.
- [ ] 5.4 Validate `modularise-auth-management-cli` with OpenSpec strict mode.
