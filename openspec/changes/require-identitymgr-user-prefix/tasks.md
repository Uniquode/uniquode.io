## 1. Parser Structure

- [x] 1.1 Add an `identitymgr user` Click group for local user operations.
- [x] 1.2 Move `create`, `update`, `delete`, `deactivate`, `list`, and
  `password` user commands under the `user` group.
- [x] 1.3 Preserve existing user command callbacks, options, arguments, output
  modes, and internal service dispatch behaviour under the new group.
- [x] 1.4 Ensure old top-level user action commands are not registered as
  aliases and fail with normal Click unknown-command errors.
- [x] 1.5 Treat command-position `help` paths as equivalent to the
  corresponding `--help` option without invoking the target operation.

## 2. Documentation And Examples

- [x] 2.1 Update README and operator examples to use
  `identitymgr user ...` for user operations.
- [x] 2.2 Update command help expectations so root help presents resource
  groups and `identitymgr user --help` presents user operations.
- [x] 2.3 Remove or update any non-archived text that presents top-level
  `identitymgr create`, `identitymgr update`, `identitymgr delete`,
  `identitymgr deactivate`, `identitymgr list`, or `identitymgr password` as
  supported commands.

## 3. Tests

- [x] 3.1 Update existing identity manager CLI tests to call user operations
  through `identitymgr user ...`.
- [x] 3.2 Add coverage that `identitymgr user --help` lists the user command
  set.
- [x] 3.3 Add coverage that top-level user action commands are rejected and do
  not invoke user operations.
- [x] 3.4 Keep existing group, scope, membership, output, password-source, and
  schema-preflight coverage passing under the new user command namespace.
- [x] 3.5 Add coverage that command-position `help` paths match the
  corresponding `--help` option.

## 4. Verification

- [x] 4.1 Run focused identity manager CLI tests.
- [x] 4.2 Run Ruff formatting and linting checks for touched files.
- [x] 4.3 Run type checking for `src/`.
- [x] 4.4 Run the full test suite.
- [x] 4.5 Validate `require-identitymgr-user-prefix` with OpenSpec strict mode.
