## Why

`wevra-identitymgr` still behaves like a standalone auth-package command: by
default it looks for `./auth.toml`, while the rest of the Wevra project
commands resolve the configured host app and load `APP_CONFIG` / `app.toml`.
This creates a split-brain configuration model where the web app and auth
operator CLI can silently use different configuration sources.

This proposal is intended to supersede the current ADR 0005 guidance that
auth operator tooling should use generic `auth.toml` configuration without
depending on a host project root. If this change is accepted, ADR 0005 must be
updated to make application config the canonical auth configuration boundary
for Wevra-hosted apps.

The broader project command model is also too permissive when no application
configuration file is resolved. Application runtime commands can fall back to
class defaults, which makes a wrongly invoked command look successful instead
of failing at the missing `app.toml` boundary. There is no user-visible notice
that baked-in defaults are being used, so a successful start can still be the
wrong start. For this project, `app.toml` is the application contract; running
without it should be explicit test-only construction, not normal command
behaviour.

## What Changes

- Make the host app config the canonical auth configuration source.
- Move auth configuration into `[auth]` and `[auth.password.policy]` sections
  in `app.toml`.
- Make `wevra-identitymgr` resolve the same host project root as other Wevra
  project commands, then load auth settings from `APP_CONFIG` or the project
  default `app.toml`.
- Make normal project commands fail fast when no `APP_CONFIG` / project
  `app.toml` can be resolved, instead of silently constructing application
  settings from built-in defaults.
- Surface an actionable configuration error that names the missing
  application-config boundary and directs the operator to run from the app
  project or set `APP_CONFIG`.
- Retire standalone `auth.toml` discovery and the `AUTH_CONFIG` environment
  variable from the project command path.
- Remove the need to pass `--config` for normal `wevra-identitymgr` usage.
- Keep `AUTH_DATABASE_URL` as the auth-specific database override, with generic
  `DATABASE_URL` as the shared database override.
- Resolve relative auth database paths relative to the loaded app config file
  directory.
- Update application defaults and documentation so runtime app settings and
  `wevra-identitymgr` consume the same `[auth]` configuration.
- Preserve explicit settings construction for tests and specialised callers;
  the fail-fast rule applies to environment/project config loading used by
  commands and default app startup.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `auth-management-cli`: Change `wevra-identitymgr` configuration resolution from
  standalone auth config files to host application config resolution.
- `identity-authentication`: Make `[auth]` in application config the canonical
  source for reusable auth runtime and policy settings.
- `environment-configuration`: Require resolved application configuration for
  normal project command and default startup settings loading.
- `application-infrastructure`: Keep the workspace root as a coordinator while
  requiring application commands to resolve the concrete app project and its
  `app.toml`.

## Impact

- Affected code is expected to include Wevra auth settings loading,
  `wevra-identitymgr` command setup, application settings loading, committed
  configuration files, tests, and documentation.
- `auth.toml`, `AUTH_CONFIG`, and normal `--config`-based operation are removed
  rather than retained as legacy compatibility because there are no released
  users to preserve.
- Existing local config should be folded into `app/app.toml`; the app project
  remains the host project root for Wevra commands in this workspace.
- Commands invoked from the workspace root may still work when Wevra can
  unambiguously resolve the `app` project and its `app.toml`; commands that
  cannot resolve an application config file should fail with an actionable
  configuration error.
