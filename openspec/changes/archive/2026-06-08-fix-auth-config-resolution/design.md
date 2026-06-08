## Context

Wevra project commands currently do not all resolve configuration through the
same boundary. Runtime and migration tooling use the host application project
and its application config, while the current `wevra-identitymgr` command still
behaves like a standalone auth command and discovers `auth.toml` from the
current working directory.

That split allows a normal operator flow to target different databases without
an obvious error. In this workspace, running commands from `app/` can leave the
runtime and migration path using the app database while identity management
loads `auth.toml` and points at a separate auth database. The result is a
successful-looking migration command followed by auth management reporting that
`identity_user` is missing.

ADR 0005 currently records the earlier standalone auth-tooling decision. This
change intentionally supersedes that part of the ADR: Wevra remains reusable,
but Wevra-hosted auth tooling is meaningful only inside a configured host
application. The host application's `app.toml` becomes the canonical
configuration contract for auth settings as well as web runtime settings.

## Goals / Non-Goals

**Goals:**

- Use one normal configuration source for app runtime, migrations, and identity
  management: `APP_CONFIG` or the resolved project `app.toml`.
- Move auth settings into `[auth]` and `[auth.password.policy]` within the
  application config file.
- Move application-owned config into `[app]`, including `[app].database_url`,
  `[app.routes]`, `[app.templates]`, and `[app.static]`.
- Allow compact route module aliases in `[app.routes]`, where hyphens in the
  module key normalise to dots at load time.
- Rename the auth operator command from `wevra-identitymgr` to
  `wevra-authmgr`.
- Make `wevra-authmgr` resolve the host application project through the same
  project-tool path as other Wevra commands.
- Fail fast when a normal project command or default app startup cannot resolve
  an application config file.
- Keep explicit settings construction available for tests and specialised
  callers that are not using project command discovery.
- Use `DATABASE_URL` as the only database environment override.
- Resolve relative configured database paths against the loaded application config
  file directory.
- Update ADR 0005, documentation, tests, and committed app config to match the
  new configuration boundary.

**Non-Goals:**

- Do not retain legacy compatibility for `auth.toml`, `AUTH_CONFIG`,
  `AUTH_DATABASE_URL`, `wevra-identitymgr`, or normal `wevra-authmgr --config`
  operation.
- Do not add an automatic migration from existing local SQLite files.
- Do not redesign migration initialisation or add `wevra-migrate init`; that is
  covered by `improve-migrate-ux`.
- Do not introduce new runtime dependencies.
- Do not make Wevra commands depend on `uniquode.io` application modules beyond
  the existing `[tool.wevra]` project metadata contract.

## Decisions

1. The host application config is the canonical auth configuration boundary.

   Auth settings will be read from the same TOML file that defines the host
   application modules, routes, templates, static paths, and runtime settings.
   This avoids split-brain operation and matches the requirement that Wevra is
   used in the context of an application.

   Alternative considered: keep `auth.toml` as an auth package config and make
   documentation clearer. That still leaves two authoritative files for one
   deployed app and does not prevent commands from targeting different
   databases.

2. `wevra-authmgr` replaces `wevra-identitymgr` as the project-tool command.

   The command will use the same project-root and `[tool.wevra]` resolution path
   as `wevra-runserver`, `wevra-migrate`, `wevra-routes`, and
   `wevra-validate`. It should load auth settings through an app-config-aware
   auth settings path rather than discovering an auth-only config file.

   The old name is removed instead of kept as an alias. The command has not
   been released as a compatibility contract, and keeping both names would
   prolong stale documentation and shell-history confusion.

   Alternative considered: keep `wevra-identitymgr` independent and require
   operators to pass `--config`. That preserves the exact failure mode that
   triggered this change and makes routine operation depend on remembering a
   package-specific option.

3. Normal command loading is strict about application config.

   Project command entry points and default app startup should require a
   resolved application config file. If no `APP_CONFIG` or project `app.toml`
   exists, the command should raise an actionable configuration error that says
   to run from the app project or set `APP_CONFIG`.

   Explicit construction of settings objects remains valid for tests and
   specialised embedding. The strict rule applies to environment/project config
   loading used by normal commands, not to direct in-memory configuration.

   Alternative considered: emit a warning while continuing with class defaults.
   That still permits the wrong app to start successfully and makes the failure
   observable only if the operator notices the warning.

4. `auth.toml`, `AUTH_CONFIG`, and routine `--config` operation are removed.

   There are no released users to preserve, so the implementation should prefer
   a clear configuration model over compatibility branches. If stale inputs are
   still accepted by a parser or shell environment during the transition, they
   should not silently redirect normal command loading away from the app config.

   Alternative considered: keep the old inputs as aliases. That makes it harder
   to reason about the database a command will use and reintroduces two config
   roots.

5. Database override precedence remains explicit.

   Application database URL resolution should use generic `DATABASE_URL`, then
   `[app].database_url` from the loaded app config. Auth tooling uses that
   same application database URL instead of defining an auth-owned database
   field. There is no auth-specific environment override because that would
   reintroduce a second routine database-selection path outside the application
   config boundary.
   Relative SQLite database paths in config are resolved relative to the app
   config file directory so `app/app.toml` remains relocatable with its app
   assets.

   Alternative considered: keep `AUTH_DATABASE_URL` for auth-only automation.
   That preserves one of the escape hatches that made local behaviour hard to
   reason about, so it is removed with the rest of the standalone auth config
   model.

   Application-wide sections use an `[app]` namespace so the committed config
   reads as one compact application document instead of a set of global
   tables. Route module keys in `[app.routes]` may use hyphens as TOML-friendly
   aliases for Python module dots; only the outer route module key is
   normalised, and duplicate aliases that resolve to the same module are
   rejected.

6. The cross-repository sequence remains Wevra first.

   The reusable loader, CLI, and tests belong in `wevra/`. After the Wevra side
   lands on `wevra:main`, the `uniquode.io` app can merge auth config into
   `app/app.toml`, remove `app/auth.toml`, update docs and ADRs, and verify
   against the updated local checkout.

   Alternative considered: pin a Wevra feature branch from the app PR. The
   project has already chosen to keep CI consuming `wevra:main` for this
   workspace, so the app PR should wait for the reusable change to land.

## Risks / Trade-offs

- Existing local development commands that still expect `auth.toml` will fail
  or target the wrong file until the config is folded into `app.toml` ->
  update the committed app config, docs, and error messages in the same change.
- Strict app-config loading may break tests that relied on missing config
  defaults -> keep explicit settings construction for tests and update command
  tests to create a real project config.
- Existing local SQLite files may contain data under the old split config ->
  treat manual data migration or file cleanup as an operator concern outside
  this change.
- Migration UX can still be unclear when a database is uninitialised -> keep
  that problem in the separate `improve-migrate-ux` change rather than mixing
  command discovery with database lifecycle design.
- The change spans Wevra and the app repository -> implement and merge Wevra
  first, then update the app against `wevra:main`.

## Migration Plan

1. Update Wevra auth settings loading so it can consume `[auth]` from the
   resolved app config file.
2. Rename `wevra-identitymgr` to `wevra-authmgr`, use project-tool resolution,
   and remove normal auth-only config discovery from its command path.
3. Make default project command/app startup settings loading fail when no app
   config file is resolved.
4. Add Wevra tests for app-config auth loading, missing app config failure,
   database URL precedence, and relative database path resolution.
5. Merge the Wevra branch before updating the app repository.
6. Fold `app/auth.toml` into `app/app.toml`, remove the standalone file, and
   update docs plus ADR 0005.

Rollback is to revert the Wevra command/loading change and app config merge
together. Partial rollback would restore the split-brain behaviour, so the two
repository changes should not be left half-applied.

## Open Questions

None for the current implementation slice. The separate migration
initialisation UX remains open under `improve-migrate-ux`.
