## Why

`identitymgr` now manages users, groups, and scopes, but user operations still
occupy the top-level command namespace while group and scope operations are
resource-prefixed. Requiring a `user` prefix makes the command tree consistent
before any release creates legacy command compatibility obligations.

## What Changes

- **BREAKING**: Move user-management commands from top-level actions to the
  `identitymgr user ...` command namespace.
- Remove top-level `identitymgr create`, `identitymgr update`,
  `identitymgr delete`, `identitymgr deactivate`, `identitymgr list`, and
  `identitymgr password` commands rather than adding compatibility aliases.
- Keep user command names, options, arguments, output formats, and service
  behaviours otherwise unchanged under the `user` group.
- Keep group and scope command structures unchanged.
- Update operator documentation, examples, and tests to use the canonical
  resource-oriented command tree.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `auth-management-cli`: Require user operations to be addressed through
  `identitymgr user ...` and reject the old top-level user action commands.

## Impact

- Affects the `identitymgr` CLI parser, help output, command dispatch, README
  examples, and user-management CLI tests.
- No runtime database, model, persistence, or service semantics change.
- No legacy aliases are required because the command has not been released.
