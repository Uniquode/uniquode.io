## 1. Wevra Config Loading

- [x] 1.1 Add an app-config-aware auth settings loading path that reads
  `[auth]` and `[auth.password.policy]` from the resolved application config.
- [x] 1.2 Retire standalone `auth.toml` discovery and `AUTH_CONFIG` from the
  normal auth command path.
- [x] 1.3 Implement application database URL precedence:
  `DATABASE_URL`, then `[app].database_url`.
- [x] 1.4 Resolve relative auth SQLite database paths relative to the loaded
  application config file directory.
- [x] 1.5 Make normal project command/default app startup settings loading fail
  fast when no application config file can be resolved.
- [x] 1.6 Preserve explicit in-memory settings construction for tests and
  specialised callers.
- [x] 1.7 Move application-owned TOML into `[app]`, `[app.routes]`,
  `[app.templates]`, and `[app.static]`.
- [x] 1.8 Normalise hyphenated `[app.routes]` module aliases to dotted Python
  module names and reject alias collisions.

## 2. Auth Manager Command

- [x] 2.1 Rename the package-owned auth operator script from
  `wevra-identitymgr` to `wevra-authmgr`.
- [x] 2.2 Remove the old `wevra-identitymgr` script instead of keeping a
  compatibility alias.
- [x] 2.3 Remove normal `--config` handling from the auth manager CLI.
- [x] 2.4 Load auth manager runtime state through the same Wevra project-tool
  resolution path used by other package-owned project commands.
- [x] 2.5 Update auth manager help, usage text, errors, and tests to use
  `wevra-authmgr`.

## 3. Wevra Tests

- [x] 3.1 Add tests proving `wevra-authmgr` loads `[auth]` from `APP_CONFIG` or
  a resolved project `app.toml`.
- [x] 3.2 Add tests proving `DATABASE_URL` overrides top-level
  `[app].database_url`.
- [x] 3.3 Add tests proving standalone `auth.toml`, `AUTH_CONFIG`, stale
  `[auth].database_url`, and `AUTH_DATABASE_URL` do not drive normal auth
  manager configuration.
- [x] 3.4 Add tests proving missing app config fails with an actionable
  configuration error for normal project commands/default startup.
- [x] 3.5 Add tests proving explicit settings construction remains usable
  without an app config file.

## 4. App Integration

- [x] 4.1 After the Wevra change is merged to `wevra:main`, update the local
  `wevra/` checkout to main before changing the app.
- [x] 4.2 Fold `app/auth.toml` into `app/app.toml`, with database config at
  `[app].database_url` and auth policy under `[auth]` /
  `[auth.password.policy]`.
- [x] 4.3 Remove the standalone app auth config file.
- [x] 4.4 Update app documentation and command references from
  `wevra-identitymgr` to `wevra-authmgr`.
- [x] 4.5 Update ADR 0005 so application config is the canonical auth
  configuration boundary for Wevra-hosted apps, and ADR 0002 for the renamed
  Wevra-owned command set.
- [x] 4.6 Update app tests and validation hooks for the new command name and
  strict app config boundary.

## 5. Validation

- [x] 5.1 Run focused Wevra auth settings and auth manager tests.
- [x] 5.2 Run affected Wevra lint, format, and type checks.
- [x] 5.3 Validate `fix-auth-config-resolution` with OpenSpec strict mode.
- [x] 5.4 Run affected app tests and command smoke checks against the local
  Wevra checkout.
- [x] 5.5 Run app lint, format, type checks, OpenSpec strict validation, and
  diff whitespace checks before review.
- [x] 5.6 After Wevra merge/update, rerun app checks before opening the app PR.
