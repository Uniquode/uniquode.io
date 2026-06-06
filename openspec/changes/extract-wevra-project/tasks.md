## 1. Preflight

- [ ] 1.1 Confirm `extract-wevra-framework-namespace` has reached a coherent
  local state before moving the package into a separate project.
- [ ] 1.2 Inventory all `src/wevra` files, package data, migrations, templates,
  static assets, and CLI entry points to move.
- [ ] 1.3 Inventory Wevra-owned tests and application integration tests to split.
- [ ] 1.4 Inventory runtime and development dependencies used by `wevra` versus
  those used only by `uniquode`.
- [ ] 1.5 Confirm the intended adjacent project path is `../wevra`.

## 2. Create The Wevra Project

- [ ] 2.1 Create the adjacent `../wevra` project directory with a `src/` layout.
- [ ] 2.2 Move `src/wevra/` from `uniquode` to `../wevra/src/wevra/`.
- [ ] 2.3 Add `../wevra/pyproject.toml` with package metadata, `uv_build`, build
  module configuration, dependencies, dev dependencies, Ruff, ty, and pytest
  settings.
- [ ] 2.4 Move Wevra README/package documentation into the new project.
- [ ] 2.5 Ensure package data includes templates, static assets, Alembic
  migration infrastructure, and module-owned auth migration revisions.
- [ ] 2.6 Initialise `../wevra` as a Git repository.

## 3. Move Tests

- [ ] 3.1 Move `test_wevra_web.py`, `test_wevra_db.py`, `test_wevra_auth.py`,
  and `test_wevra_namespace.py` into `../wevra/tests/`.
- [ ] 3.2 Move framework-owned validation, command, route, rendering,
  persistence, and identity CLI tests out of application test files where
  practical.
- [ ] 3.3 Keep `uniquode` tests focused on application integration, settings,
  startup, app routes, app templates, and project command adapters.
- [ ] 3.4 Add or adjust Wevra tests proving `wevra` does not import
  `uniquode`.
- [ ] 3.5 Add or adjust Uniquode tests proving the app imports `wevra` from the
  dependency and no longer builds local framework source.

## 4. Update Uniquode Dependency Metadata

- [ ] 4.1 Add `wevra` to `uniquode` project dependencies.
- [ ] 4.2 Add `wevra = { path = "../wevra", editable = true }` to
  `[tool.uv.sources]`.
- [ ] 4.3 Remove `wevra` from the `uniquode` build backend module list.
- [ ] 4.4 Remove framework-only runtime dependencies from `uniquode` when they
  are supplied transitively by `wevra`, while keeping application-owned
  dependencies explicit.
- [ ] 4.5 Refresh `uv.lock` so the editable sibling dependency is resolved.
- [ ] 4.6 Confirm project scripts still point to `wevra.tools.*` and
  `wevra.auth.cli.identitymgr` where the application intentionally exposes
  those commands.

## 5. Update Paths, Docs, And OpenSpec

- [ ] 5.1 Update README and local development documentation to explain the
  adjacent `uniquode` and `wevra` checkout shape.
- [ ] 5.2 Update OpenSpec live references that describe `wevra` as
  application-local source.
- [ ] 5.3 Update validation/test path assumptions that point at
  `src/wevra/...` inside `uniquode`.
- [ ] 5.4 Update stale-import/package-boundary tests in both projects.
- [ ] 5.5 Update `.todo/context.md` with the new project boundary and
  validation results.

## 6. Validate Wevra

- [ ] 6.1 Run `uv run pytest -q` from `../wevra`.
- [ ] 6.2 Run Ruff format and lint checks from `../wevra`.
- [ ] 6.3 Run `ty check src/` from `../wevra`.
- [ ] 6.4 Build the Wevra wheel from `../wevra` to verify package data.
- [ ] 6.5 Inspect the built wheel for templates, static assets, Alembic
  migration files, and auth migration revisions.

## 7. Validate Uniquode

- [ ] 7.1 Run `uv sync` or equivalent from `uniquode` to install editable
  `../wevra`.
- [ ] 7.2 Run focused application integration tests that import and exercise
  editable `wevra`.
- [ ] 7.3 Run `uv run pytest -q` from `uniquode`.
- [ ] 7.4 Run Ruff format and lint checks from `uniquode`.
- [ ] 7.5 Run `ty check src/` from `uniquode`.
- [ ] 7.6 Run strict OpenSpec validation for `extract-wevra-project`.
- [ ] 7.7 Run strict main spec validation.
- [ ] 7.8 Run `git diff --check` in both repositories.

## 8. Publish Wevra

- [ ] 8.1 Commit the extracted `wevra` project in `../wevra`.
- [ ] 8.2 Create the GitHub repository for `wevra`.
- [ ] 8.3 Push the `wevra` repository to GitHub.
- [ ] 8.4 Record the GitHub repository URL in Wevra documentation and, if
  useful, Uniquode documentation.
- [ ] 8.5 Leave CI setup out of scope unless explicitly requested later.
