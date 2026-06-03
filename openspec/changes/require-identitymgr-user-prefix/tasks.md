## 1. Parser Structure

- [ ] 1.1 Add an `identitymgr user` Click group for local user operations.
- [ ] 1.2 Move `create`, `update`, `delete`, `deactivate`, `list`, and
  `password` user commands under the `user` group.
- [ ] 1.3 Preserve existing user command callbacks, options, arguments, output
  modes, and internal service dispatch behaviour under the new group.
- [ ] 1.4 Ensure old top-level user action commands are not registered as
  aliases and fail with normal Click unknown-command errors.

## 2. Documentation And Examples

- [ ] 2.1 Update README and operator examples to use
  `identitymgr user ...` for user operations.
- [ ] 2.2 Update command help expectations so root help presents resource
  groups and `identitymgr user --help` presents user operations.
- [ ] 2.3 Remove or update any non-archived text that presents top-level
  `identitymgr create`, `identitymgr update`, `identitymgr delete`,
  `identitymgr deactivate`, `identitymgr list`, or `identitymgr password` as
  supported commands.

## 3. Tests

- [ ] 3.1 Update existing identity manager CLI tests to call user operations
  through `identitymgr user ...`.
- [ ] 3.2 Add coverage that `identitymgr user --help` lists the user command
  set.
- [ ] 3.3 Add coverage that top-level user action commands are rejected and do
  not invoke user operations.
- [ ] 3.4 Keep existing group, scope, membership, output, password-source, and
  schema-preflight coverage passing under the new user command namespace.

## 4. Verification

- [ ] 4.1 Run focused identity manager CLI tests.
- [ ] 4.2 Run Ruff formatting and linting checks for touched files.
- [ ] 4.3 Run type checking for `src/`.
- [ ] 4.4 Run the full test suite.
- [ ] 4.5 Validate `require-identitymgr-user-prefix` with OpenSpec strict mode.
