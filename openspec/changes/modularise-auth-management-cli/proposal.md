## Why

Linear: [UT-226](https://linear.app/uniquode/issue/UT-226/modularise-auth-management-cli)

`src/wevra/auth/cli/identitymgr.py` is now large enough that command registration,
dispatch, schema checks, output formatting, and resource-specific command
definitions are difficult to evolve together. Splitting the CLI into explicit
components will make future extended-authentication operations easier to add
without changing the operator-facing command contract.

## What Changes

- Convert `wevra.auth.cli.identitymgr` from a single module into a package while
  preserving the public project-script entry point `wevra.auth.cli.identitymgr:main`.
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

None.

### Modified Capabilities

- `auth-management-cli`: Defines the internal package composition and explicit
  command-registration contract for the current `identitymgr` CLI.

## Impact

- Affects `src/wevra/auth/cli/identitymgr.py`, the `wevra.auth.cli.identitymgr` import
  boundary, CLI command registration, and auth-management CLI tests.
- The project script remains `identitymgr = "wevra.auth.cli.identitymgr:main"`.
- No database, persistence, identity-service, or operator-facing CLI behaviour
  changes are intended.
- No automatic plugin discovery is introduced; future extension mechanisms can
  be proposed separately when concrete requirements exist.
