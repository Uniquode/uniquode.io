## Context

Reusable web, data, tooling, and auth infrastructure has already been separated
from `uniquode`, but the current top-level packages are temporary names and
several modules have grown into broad catch-all files. The Wevra namespace
refactor should use the rename as the point where reusable ownership boundaries
become explicit.

This is mostly refactoring work, but package discovery, package data, Alembic
version locations, CLI entry points, and import-boundary tests make the change
behaviourally sensitive. The implementation should preserve existing runtime
behaviour while making module ownership easier to extend.

## Goals

- Move reusable infrastructure into a `wevra` namespace.
- Keep `uniquode` as the concrete host application package.
- Split broad reusable modules into packages where the ownership boundary is
  already clear or where near-term growth is likely.
- Preserve existing runtime, migration, validation, rendering, route, static,
  auth, and CLI behaviour.
- Keep package-data discovery explicit and testable.
- Avoid compatibility shims unless a concrete pre-publication consumer requires
  them.

## Non-Goals

- Do not change user-facing behaviour.
- Do not rename the `identitymgr` command in this change.
- Do not redesign authentication policy, authorisation semantics, or migration
  revision IDs.
- Do not introduce new runtime dependencies.
- Do not keep temporary top-level package aliases merely for convenience.

## Proposed Package Structure

Use a single `wevra` source package with functional subpackages:

```text
src/wevra/
  __init__.py

  core/
    composition/
    diagnostics.py
    resources.py
    settings.py

  web/
    context.py
    csrf.py
    errors/
    forms/
    rendering/
    routes/
    staticfiles/
    templating/
    theme/
    validation/
    views/
    static/
    templates/

  db/
    urls.py
    migrations/
    models.py
    persistence.py
    surfaces.py

  auth/
    accounts/
    admin/
    authorisation/
    cli/
    delivery.py
    mfa/
    models/
    persistence/
    routes/
    sessions/
    templates/
    migrations/

  tools/
    migrate.py
    project.py
    runserver.py
    validate.py
    validation/
```

The exact file split can be adjusted during implementation, but this structure
sets the ownership direction.

## Core Package

`wevra.core` should contain framework-wide utilities that are not inherently
HTTP, SQLAlchemy, or auth specific:

- application composition config loading;
- reusable conventions and surface-name constants;
- diagnostic error-message helpers;
- package-resource path helpers;
- generic composed-settings loading.

The current `wevra.core.composition`, `wevra.core.conventions`,
`wevra.core.diagnostics`, `wevra.core.resources`, and reusable settings-loading
logic should move here unless they depend directly on FastAPI/Jinja/Starlette
types.

## Web Package

`wevra.web` should own HTTP, FastAPI, Starlette, Jinja, template, static,
theme, CSRF, route, and view infrastructure.

### Routes

`wevra.web.routes`, `route_contract`, `routing`, and route-surface discovery
should become a package rather than a set of broad modules:

```text
wevra/web/routes/
  __init__.py
  contracts.py
  definitions.py
  discovery.py
  registration.py
  builtins.py
```

The package should separate:

- route constants and public contract types;
- route/view definitions;
- configured-module route discovery;
- FastAPI registration/collision validation;
- Wevra-owned built-in routes such as theme endpoints.

### Static And Templates

Package data should stay under `wevra.web`, not the top-level `wevra` package.
These assets are web-framework defaults and should be discovered by including
`wevra.web` in the configured module list.

Use non-conflicting code package names for implementation modules:

```text
wevra/web/static/       # package data served/exported as static assets
wevra/web/templates/    # package data loaded by Jinja
wevra/web/staticfiles/  # Python code for serving/export
wevra/web/templating/   # Python code for template loading/rendering helpers
```

This avoids putting `__init__.py` files inside directories that are exported as
static/template resource roots. Resource export must not accidentally include
Python package files as static assets.

### Views

`views` should become a package because view styles are expected to expand:

```text
wevra/web/views/
  __init__.py
  base.py
  templates.py
```

The first slice can keep only the current template view helper, but the package
shape should allow later JSON, redirect, HTMX partial, or form-oriented view
helpers without crowding one file.

### Errors, Theme, Validation, Forms

The current larger modules should become packages when the split is mechanical
and ownership is clear:

- `errors/` for page, partial, API, and fallback error handling;
- `theme/` for mode parsing, state, routes/views, and cookies;
- `validation/` for web validation target definitions and checks;
- `forms/` for CSRF and form-security helpers if they continue to grow
  together.

## DB Package

`wevra.db` should own the reusable SQLAlchemy/Alembic support. The current
Alembic `env.py` has already been made application-independent: it reads
Alembic config values and configured module metadata rather than importing the
host application.

Keep the generic Alembic script environment under:

```text
wevra/db/migrations/
  env.py
  script.py.mako
  README.md
```

The host application still owns concrete defaults such as database URL,
configured modules, and whether `alembic.ini` remains as a root-level adapter.
Module-owned revision files stay beside the modules whose models they migrate,
such as `wevra.auth.migrations.versions`.

## Auth Package

`wevra.auth` should not be a flat rename of the previous auth package. The
current package has clear functional slices and two large files (`identitymgr.py` and
`management.py`) that should be split while imports are already being updated.

Proposed direction:

```text
wevra/auth/
  accounts/
    lifecycle.py
    manager.py
    passwords.py
    schemas.py
    bootstrap.py
  admin/
    records.py
    users.py
    groups.py
    scopes.py
  authorisation/
    groups.py
    scopes.py
    effective.py
  cli/
    identitymgr.py
    parsing.py
    rendering.py
  mfa/
    challenges.py
    recovery.py
    totp.py
    webauthn.py
  persistence/
    database.py
    stores.py
  routes/
    pages.py
    api.py
    wiring.py
  sessions/
    backends.py
    cookies.py
  models/
  migrations/
  templates/
```

The first implementation does not need to perfectly decompose every function,
but it should avoid carrying obviously overloaded files into the new namespace.
In particular:

- CLI parsing/rendering should move out of the auth management service layer;
- effective-scope resolution should be a reusable authorisation service, not
  only a management command helper;
- auth routes should be split by surface/wiring instead of remaining one broad
  module;
- placeholder MFA modules can remain small, but should live under `mfa`.

## Tools Package

`wevra.tools` should own reusable project CLI adapters such as `migrate`,
`runserver`, and `validate`. Host-specific settings still come from the host
application through loaders/adapters.

Expected script targets:

```toml
migrate = "wevra.tools.migrate:main"
runserver = "wevra.tools.runserver:main"
validate = "wevra.tools.validate:main"
identitymgr = "wevra.auth.cli.identitymgr:main"
```

## Composition And Module Names

Configured module names should move from temporary top-level packages to Wevra
packages. Expected default direction:

```toml
modules = ["uniquode", "wevra.web", "wevra.auth"]
```

The exact ordering remains significant: earlier modules override later
template/static resources. The host application should remain free to omit
optional Wevra modules that it does not use.

## Testing Strategy

Tests should use Wevra-oriented names for the reusable web, DB, and auth
surfaces. `test_identitymgr.py` can keep its name because it tests the public
CLI.

Required coverage:

- import-boundary tests proving `wevra.*` packages do not import `uniquode`;
- stale-import tests proving live source/tests no longer import legacy
  reusable package roots;
- configured-module discovery tests for `uniquode`, `wevra.web`, and
  `wevra.auth`;
- package-resource tests for Wevra templates and static assets;
- route composition and collision tests after the route package split;
- validation discovery tests after moving `wevra.tools.validation`;
- Alembic metadata and version-location tests with unchanged revision IDs;
- migration-from-empty-database tests;
- CLI smoke tests for `migrate`, `runserver`, `validate`, and `identitymgr`.

## Edge Cases

- Empty old package directories must be removed, otherwise Python namespace
  package discovery can still find stale modules.
- Static export must not include Python files from code packages.
- Existing Alembic revision IDs and dependency pointers must not change.
- Root `alembic.ini` may still be an application adapter, but it must point to
  the reusable Wevra DB script environment.
- Archived OpenSpec history may keep old names; live docs/specs/tests should
  use Wevra names.
- `app.toml`, README examples, and validation messages must agree on configured
  module names.
