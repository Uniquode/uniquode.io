## Why

`src/auth_ext/identitymgr.py` is now large enough that command registration,
dispatch, schema checks, output formatting, and resource-specific command
definitions are difficult to evolve together. Splitting the CLI into explicit
components will make future extended-authentication operations easier to add
without changing the operator-facing command contract.

## What Changes

- Convert `auth_ext.identitymgr` from a single module into a package while
  preserving the public project-script entry point `auth_ext.identitymgr:main`.
- Split root CLI construction, user commands, group commands, scope commands,
  schema checks, command arguments, and output formatting into focused modules.
- Add an explicit registration boundary where each command component registers
  itself with the root Click command tree.
- Prefer registration over automatic command discovery or plugin loading for
  this change.
- Keep existing `identitymgr` command names, options, help output, output
  formats, validation behaviour, and exit-status semantics unchanged.
- Avoid new runtime dependencies or framework structure beyond the package
  split required by the refactor.

## Capabilities

### New Capabilities

- `identitymgr-cli-composition`: Defines the internal package composition and
  explicit command-registration contract for the `identitymgr` CLI.

### Modified Capabilities

None.

## Impact

- Affects `src/auth_ext/identitymgr.py`, the `auth_ext.identitymgr` import
  boundary, CLI command registration, and identity-manager CLI tests.
- The project script remains `identitymgr = "auth_ext.identitymgr:main"`.
- No database, persistence, identity-service, or operator-facing CLI behaviour
  changes are intended.
- No automatic plugin discovery is introduced; future extension mechanisms can
  be proposed separately when concrete requirements exist.
