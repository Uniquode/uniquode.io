## 1. Preflight And Inventory

- [x] 1.1 Capture the package/import surface for the temporary reusable
  packages, `uniquode`, scripts,
  `app.toml`, and `alembic.ini`.
- [x] 1.2 Identify all live imports of temporary package names in source,
  tests, README, OpenSpec live specs, and configuration files.
- [x] 1.3 Identify package data roots for templates, static assets, and
  migration versions before moving files.
- [x] 1.4 Confirm archived OpenSpec changes are excluded from stale-import
  cleanup checks.

## 2. Wevra Package Skeleton

- [x] 2.1 Create the `wevra` package and top-level subpackages for `core`,
  `web`, `db`, `auth`, and `tools`.
- [x] 2.2 Update packaging metadata so `wevra` replaces the temporary reusable
  top-level packages in the build surface.
- [x] 2.3 Keep `uniquode` as the host/application package and fold public page
  content into it rather than moving application content under `wevra`.
- [x] 2.4 Remove empty old package directories after moves so Python namespace
  package discovery cannot find stale modules.

## 3. Core Package

- [x] 3.1 Move reusable composition loading into `wevra.core.composition`.
- [x] 3.2 Move framework conventions and surface-name constants into
  `wevra.core.conventions`.
- [x] 3.3 Move diagnostic message helpers into `wevra.core.diagnostics`.
- [x] 3.4 Move package-resource helpers into `wevra.core.resources`.
- [x] 3.5 Move generic composed-settings loading into `wevra.core.settings`.
- [x] 3.6 Update framework imports that consume core helpers.

## 4. Web Package

- [x] 4.1 Create `wevra.web` package structure for context, routes, rendering,
  templating, static files, views, errors, forms, theme, and validation.
- [x] 4.2 Move route constants, definitions, module route containers, discovery,
  and FastAPI registration into `wevra.web.routes` submodules.
- [x] 4.3 Move built-in Wevra web routes such as theme routes into the route
  package without changing route names or paths.
- [x] 4.4 Move template loading and rendering helpers into
  `wevra.web.templating` / `wevra.web.rendering`.
- [x] 4.5 Move view helpers into `wevra.web.views`, preserving the existing
  template view behaviour while allowing future view styles.
- [x] 4.6 Move static serving/export code into `wevra.web.staticfiles`.
- [x] 4.7 Move reusable web templates under `wevra/web/templates` as package
  data.
- [x] 4.8 Move reusable web static assets under `wevra/web/static` as package
  data.
- [x] 4.9 Move CSRF and form-security helpers into `wevra.web.forms` or the
  final web security package chosen during implementation.
- [x] 4.10 Move error handling into `wevra.web.errors` without changing page,
  partial, API, or fallback error semantics.
- [x] 4.11 Move theme mode parsing, cookie handling, route views, and state
  helpers into `wevra.web.theme`.
- [x] 4.12 Move reusable web validation targets and checks into
  `wevra.web.validation`.

## 5. DB Package

- [x] 5.1 Move database URL helpers into `wevra.db.urls`.
- [x] 5.2 Move SQLAlchemy base model metadata into `wevra.db.models`.
- [x] 5.3 Move persistence/session helpers into `wevra.db.persistence`.
- [x] 5.4 Move data surface discovery into `wevra.db.surfaces`.
- [x] 5.5 Move migration metadata composition into
  `wevra.db.migration_metadata`.
- [x] 5.6 Move generic Alembic command construction into `wevra.db.migrate` or
  the final DB command-support module.
- [x] 5.7 Move generic Alembic `env.py`, `script.py.mako`, and migration README
  into `wevra/db/migrations`.
- [x] 5.8 Preserve existing Alembic revision IDs and dependency pointers.
- [x] 5.9 Update Alembic script location and version-location composition for
  the Wevra DB package.

## 6. Auth Package

- [x] 6.1 Create `wevra.auth` subpackages for accounts, admin, authorisation,
  CLI, MFA, persistence, routes, sessions, models, migrations, and templates.
- [x] 6.2 Move account lifecycle, bootstrap, manager, schema, and password
  policy code into the accounts package.
- [x] 6.3 Move group, scope, user-management, and record-formatting services
  into admin and authorisation packages with clear runtime/management
  separation.
- [x] 6.4 Move effective-scope resolution into reusable authorisation services
  rather than keeping it only in management helpers.
- [x] 6.5 Move the `identitymgr` CLI into `wevra.auth.cli` while preserving the
  public `identitymgr` script name and command behaviour.
- [x] 6.6 Split CLI parsing/rendering helpers out of the auth management service
  layer where practical.
- [x] 6.7 Move MFA placeholder and challenge modules under `wevra.auth.mfa`.
- [x] 6.8 Move session backends, cookies, and current-user helpers into
  `wevra.auth.sessions`.
- [x] 6.9 Move auth route wiring into `wevra.auth.routes` without changing
  mounted paths or route names.
- [x] 6.10 Move auth templates under `wevra/auth/templates` as package data.
- [x] 6.11 Move auth models and module-owned migration versions under
  `wevra.auth`.

## 7. Tools And Host Adapters

- [x] 7.1 Move reusable CLI adapters into `wevra.tools`.
- [x] 7.2 Update project script entry points for `migrate`, `runserver`,
  `validate`, and `identitymgr`.
- [x] 7.3 Preserve host-specific settings loading through explicit adapters
  rather than importing host settings from generic tool modules.
- [x] 7.4 Update `uniquode` imports to consume Wevra framework packages.
- [x] 7.5 Keep `uniquode` focused on host settings, startup wiring, health
  routes, and application-specific validation.

## 8. Composition And Configuration

- [x] 8.1 Update default configured modules from temporary package names to
  Wevra package names.
- [x] 8.2 Update `app.toml` module names and package-resource expectations.
- [x] 8.3 Update `alembic.ini` defaults to point at the Wevra DB script
  environment and Wevra module names.
- [x] 8.4 Update README and live OpenSpec references to use Wevra names.
- [x] 8.5 Ensure archived OpenSpec history remains historical and is not
  rewritten for the namespace refactor.

## 9. Tests

- [x] 9.1 Rename or reorganise web tests around `wevra.web`.
- [x] 9.2 Rename or reorganise DB tests around `wevra.db`.
- [x] 9.3 Rename or reorganise auth tests around `wevra.auth` while preserving
  identity CLI coverage.
- [x] 9.4 Add import-boundary tests proving `wevra.*` packages do not import
  `uniquode`.
- [x] 9.5 Add stale-import tests for live source/tests and active OpenSpec docs
  to reject legacy reusable package imports.
- [x] 9.6 Update configured-module discovery tests for `uniquode`,
  `wevra.web`, and `wevra.auth`.
- [x] 9.7 Update package-resource tests for Wevra templates and static assets.
- [x] 9.8 Update route composition and collision tests after the route package
  split.
- [x] 9.9 Update validation discovery tests for `wevra.tools.validation` and
  moved validation targets.
- [x] 9.10 Update Alembic metadata, version-location, and migrate-from-empty
  database tests.
- [x] 9.11 Update CLI smoke tests for migrated script targets.

## 10. Validation

- [x] 10.1 Run focused Wevra web, DB, auth, identity CLI, app, and validation
  tests after the namespace move.
- [x] 10.2 Run full Python test suite.
- [x] 10.3 Run ruff format and lint checks.
- [x] 10.4 Run the type checker over `src/`.
- [x] 10.5 Run strict OpenSpec validation for
  `extract-wevra-framework-namespace`.
- [x] 10.6 Run strict main spec validation.
- [x] 10.7 Run `git diff --check`.
