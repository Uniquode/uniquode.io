## Overview

The CLI rename is a direct breaking rename from `usermgr` to `identitymgr`.
Because the project is still WIP and unpublished, this change does not preserve
a compatibility script or import alias.

## Decisions

- The project script is `identitymgr`, pointing at `auth_ext.identitymgr:main`.
- The implementation module is `auth_ext.identitymgr`.
- Click uses `identitymgr` as the program name so help, usage errors, and CLI
  exceptions all present the new command name.
- Tests import `auth_ext.identitymgr` directly and assert that `usermgr` is not
  present in project scripts.
- Historical archived OpenSpec changes remain historical records and are not
  rewritten for the rename.

## Impact

Operators must update local commands and automation from `usermgr` to
`identitymgr`.
