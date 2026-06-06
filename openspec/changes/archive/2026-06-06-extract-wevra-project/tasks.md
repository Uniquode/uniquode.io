## 1. Preflight

- [x] 1.1 Confirm `extract-wevra-framework-namespace` has reached a coherent
  local state before moving the package into a separate project.
- [x] 1.2 Inventory all `src/wevra` files, package data, migrations, templates,
  static assets, and CLI entry points to move.
- [x] 1.3 Inventory Wevra-owned tests and application integration tests to split.
- [x] 1.4 Inventory runtime and development dependencies used by `wevra` versus
  those used only by `uniquode`.
- [x] 1.5 Confirm the intended adjacent project path is
  `uniquode/wevra`.

## 2. Create The Wevra Project

- [x] 2.1 Create `uniquode/wevra` as a history-filtered clone using
  `git-filter-repo`.
- [x] 2.2 Keep current `src/wevra/`, historical reusable package paths, and
  Wevra-owned tests/docs in the filtered repository, then clean it into a
  standalone `src/wevra/` project layout.
- [x] 2.3 Add `wevra/pyproject.toml` with package metadata, `uv_build`, build
  module configuration, dependencies, dev dependencies, Ruff, ty, and pytest
  settings.
- [x] 2.4 Move Wevra README/package documentation into the new project.
- [x] 2.5 Ensure package data includes templates, static assets, Alembic
  migration infrastructure, and module-owned auth migration revisions.
- [x] 2.6 Confirm `wevra` remains an independent Git repository with
  filtered framework history.

## 3. Move Tests

- [x] 3.1 Move `test_wevra_web.py`, `test_wevra_db.py`, `test_wevra_auth.py`,
  and `test_wevra_namespace.py` into `wevra/tests/`.
- [x] 3.2 Move framework-owned validation, command, route, rendering,
  persistence, and identity CLI tests out of application test files where
  practical.
- [x] 3.3 Keep `uniquode` tests focused on application integration, settings,
  startup, app routes, app templates, and project command adapters.
- [x] 3.4 Add or adjust Wevra tests proving `wevra` does not import
  `uniquode`.
- [x] 3.5 Add or adjust Uniquode tests proving the app imports `wevra` from the
  dependency and no longer builds local framework source.

## 4. Update Uniquode Dependency Metadata

- [x] 4.1 Add `wevra` to `uniquode` project dependencies.
- [x] 4.2 Add a parent `uv` workspace that resolves `uniquode` and `wevra` as
  workspace members.
- [x] 4.3 Remove `wevra` from the `uniquode` build backend module list.
- [x] 4.4 Remove framework-only runtime dependencies from `uniquode` when they
  are supplied transitively by `wevra`, while keeping application-owned
  dependencies explicit.
- [x] 4.5 Refresh the parent workspace `uv.lock` so both member projects share
  one dependency resolution.
- [x] 4.6 Confirm project scripts still point to `wevra.tools.*` and
  `wevra.auth.cli.identitymgr` where the application intentionally exposes
  those commands.

## 5. Update Paths, Docs, And OpenSpec

- [x] 5.1 Update README and local development documentation to explain the
  adjacent `app` and `wevra` checkout shape inside `uniquode`.
- [x] 5.2 Keep OpenSpec artifacts in `uniquode` and update live references that
  describe `wevra` as application-local source.
- [x] 5.3 Update validation/test path assumptions that point at
  `src/wevra/...` inside `uniquode`.
- [x] 5.4 Update stale-import/package-boundary tests in both projects.
- [x] 5.5 Update `.todo/context.md` with the new project boundary and
  validation results.

## 6. Coordinate Workspace Dependencies

- [x] 6.1 Add root workspace metadata with `app` as the application member and
  temporary local `wevra` source support while Wevra is not yet a regular
  dependency.
- [x] 6.2 Move application and temporary local Wevra dependency resolution to
  the root `uv.lock`.
- [x] 6.3 Remove member-local lock files for the coordinated workspace flow.
- [x] 6.4 Document that application tests should run with `app` as `cwd` while
  still using the parent workspace lock.
- [x] 6.5 Verify `uv workspace list` discovers the workspace from the parent and
  app member.

## 7. Validate Wevra Extraction

- [x] 7.1 Confirm Wevra-owned tests, linting, type checks, and package-build
  checks live in the `wevra` repository rather than in this repository's
  routine validation gates.
- [x] 7.2 Verify this repository does not run Wevra-owned tests, linting, or
  type checks from root CI or pre-commit.
- [x] 7.3 Keep this repository's validation focused on application integration
  with the `wevra` dependency.
- [x] 7.4 Prune the Wevra Vulture whitelist to Wevra-owned framework hooks.

## 8. Validate App

- [x] 8.1 Run `uv sync` or equivalent from `app` to install workspace
  `wevra`.
- [x] 8.2 Run focused application integration tests that import and exercise
  workspace `wevra`.
- [x] 8.3 Run `uv run pytest -q` from `app`.
- [x] 8.4 Run Ruff format and lint checks from `app`.
- [x] 8.5 Run `ty check src/` from `app`.
- [x] 8.6 Run strict OpenSpec validation for `extract-wevra-project`.
- [x] 8.7 Run strict main spec validation.
- [x] 8.8 Run `git diff --check` in this repository.
- [x] 8.9 Prune the application Vulture whitelist to application-owned dynamic
  hooks.
- [x] 8.10 Add the application `validate` command to pre-commit as a
  composition/configuration backstop.

## 9. Publish Wevra

- [x] 9.1 Commit the extracted `wevra` project in `wevra`.
- [x] 9.2 Create the public GitHub repository `Uniquode/wevra`.
- [x] 9.3 Push the `wevra` repository to GitHub.
- [x] 9.4 Record the GitHub repository URL in Wevra documentation and, if
  useful, Uniquode documentation.
- [x] 9.5 Leave CI setup out of scope unless explicitly requested later.

## 10. Configure Wevra Repository Automation

- [x] 10.1 Add Wevra-owned GitHub Actions for tests, linting, type checking,
  package build, and CodeQL analysis.
- [x] 10.2 Add Wevra Dependabot configuration for GitHub Actions and `uv`.
- [x] 10.3 Add Wevra Dependabot auto-merge workflow for `uv` semver patch
  updates.
- [x] 10.4 Add a Wevra-local `.pre-commit-config.yaml` adapted from this
  repository's checks.
- [x] 10.5 Push the Wevra automation files to `Uniquode/wevra`.
- [x] 10.6 Mirror `uniquode.io` merge settings, main branch protection, and
  required-check ruleset onto `Uniquode/wevra`.
