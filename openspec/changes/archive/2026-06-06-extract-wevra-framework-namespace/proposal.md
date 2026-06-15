## Why

Linear: [UT-217](https://linear.app/uniquode/issue/UT-217/extract-wevra-framework-namespace)

Reusable web, data, settings, tooling, and auth infrastructure has been split
out of `uniquode`, but it still lives in temporary top-level packages. Before
the project exposes much application-specific behaviour, we should capture the
planned move into the named `wevra` framework namespace.

## What Changes

- **BREAKING** Replace the temporary reusable top-level packages with explicit
  `wevra.*` packages after the current boundary separation is reviewed.
- Keep `uniquode` focused on the concrete application and its policy, settings,
  health route, and application-specific validation.
- Preserve existing runtime, validation, migration, rendering, route
  composition, static asset, and auth behaviours while changing import paths,
  script entry points, package data paths, configured module names, docs, specs,
  and tests.
- Avoid compatibility shims unless the design phase identifies a concrete need
  before publication.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `application-infrastructure`: define the `wevra` framework namespace and keep
  the host application package separate from reusable framework packages.
- `environment-configuration`: move reusable settings-loading mechanics from
  the temporary web core package into the `wevra` namespace.
- `web-foundation`: move reusable web runtime, route, renderer, template,
  static, theme, error, CSRF, and web-validation contracts into `wevra`.
- `development-database`: move reusable SQLAlchemy, database URL, session, and
  Alembic migration infrastructure into `wevra`.
- `auth-ext-package`: align reusable auth infrastructure with the `wevra`
  namespace while preserving host-application independence.

## Impact

- Affects source package layout, imports, project scripts, `app.toml` module
  names, package data, README/OpenSpec/ADR wording, tests, and validation
  checks.
- No new runtime dependency is expected.
- Existing application behaviour and database migration graph semantics should
  remain unchanged.
