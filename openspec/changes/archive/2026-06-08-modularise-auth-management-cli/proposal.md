## Why

Linear: [UT-226](https://linear.app/uniquode/issue/UT-226/modularise-auth-management-cli)

The `wevra-authmgr` implementation currently lives behind
`src/wevra/auth/cli/identitymgr.py`, which is now large enough that command
registration, dispatch, schema checks, output formatting, and resource-specific
command definitions are difficult to evolve together. Splitting the CLI into
explicit components will make future extended-authentication operations easier
to add without changing the operator-facing command contract.

Some CLI support code is also not auth-specific. Project configuration
resolution, database URL/session setup, schema preflight wiring, and consistent
operator diagnostics are concerns that can apply to multiple Wevra commands.
Those cross-command concerns should live in shared Wevra CLI/tooling modules so
`wevra-authmgr`, `wevra-migrate`, and later commands remain aligned over time.

## What Changes

- Replace the current `wevra.auth.cli.identitymgr` implementation module with a
  `wevra.auth.cli.authmgr` package and make the public project-script entry
  point `wevra.auth.cli.authmgr:main`.
- Split root CLI construction, user commands, group commands, scope commands,
  schema checks, command arguments, and output formatting into focused modules.
- Move concrete cross-command helpers, especially database/configuration/session
  setup needed by more than one Wevra CLI, into shared Wevra tooling modules
  rather than burying them inside the auth manager package.
- Add an explicit registration boundary where each command component registers
  itself with the root Click command tree.
- Prefer registration over automatic command discovery or plugin loading for
  this change.
- Keep existing `wevra-authmgr` command names, options, help output, output
  formats, validation behaviour, and exit-status semantics unchanged.
- Avoid new runtime dependencies or framework structure beyond the package
  split required by the refactor.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `auth-management-cli`: Defines the internal package composition, shared
  CLI/tooling boundaries, and explicit command-registration contract for the
  current `wevra-authmgr` CLI.

## Impact

- Affects `src/wevra/auth/cli/identitymgr.py`, the new
  `wevra.auth.cli.authmgr` import boundary, CLI command registration, and
  auth-management CLI tests.
- The project script changes to
  `wevra-authmgr = "wevra.auth.cli.authmgr:main"`.
- No database, persistence, identity-service, or operator-facing CLI behaviour
  changes are intended.
- No automatic plugin discovery is introduced; future extension mechanisms can
  be proposed separately when concrete requirements exist.
