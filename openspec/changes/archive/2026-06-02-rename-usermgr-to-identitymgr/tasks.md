## 1. CLI Rename

- [x] 1.1 Rename the CLI module from `auth_ext.usermgr` to
  `auth_ext.identitymgr`.
- [x] 1.2 Replace the `usermgr` project script with `identitymgr` targeting the
  renamed module.
- [x] 1.3 Update Click command names, program names, usage messages, and
  operator-facing output references to `identitymgr`.
- [x] 1.4 Remove compatibility references that claim `identitymgr` is future work.

## 2. Tests And Documentation

- [x] 2.1 Rename and update user-management CLI tests to import and exercise
  `auth_ext.identitymgr`.
- [x] 2.2 Update README examples and operator documentation to use
  `identitymgr`.
- [x] 2.3 Update Vulture whitelist or framework-entry metadata for the renamed
  Click command callbacks if required.
- [x] 2.4 Run formatting, linting, type checking, the relevant test suite, and
  `openspec validate rename-usermgr-to-identitymgr --strict`.
