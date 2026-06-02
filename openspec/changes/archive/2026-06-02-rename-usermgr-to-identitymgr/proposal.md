## Why

Linear: [UT-215](https://linear.app/uniquode/issue/UT-215/rename-usermgr-to-identitymgr)

The local identity CLI now manages users, groups, scopes, memberships, and
effective scope inspection. The `usermgr` name no longer reflects its operational
surface.

## What Changes

- Rename the local operator CLI from `usermgr` to `identitymgr`.
- Move the implementation module from `auth_ext.usermgr` to
  `auth_ext.identitymgr`.
- Update command help, usage text, docs, tests, and script metadata to use
  `identitymgr`.
- Remove the `usermgr` project script rather than keeping a compatibility alias.

## Capabilities

### Modified Capabilities

- `user-management-cli`: The local identity-management CLI is exposed as
  `identitymgr` rather than `usermgr`.

## Impact

- Operators must use `identitymgr` for local identity administration.
- This is a breaking CLI rename, acceptable because the project is still WIP and
  unpublished.
