## Context

The current `extract-wevra-framework-namespace` work creates the desired import
shape:

```text
src/wevra/
  core/
  web/
  db/
  tools/
  auth/
```

That gives a package boundary, but not a project boundary. The `uniquode`
application still builds and tests `wevra` as if it were application-local
source. The next framework design work should happen in the framework project,
not as more application code.

## Target Layout

Use sibling project directories under the `uniquode` workspace root:

```text
~/Code/uniquode/
  pyproject.toml
  uv.lock
  app/
    pyproject.toml
    src/app/
    tests/
  wevra/
    pyproject.toml
    src/wevra/
    tests/
```

This keeps `wevra` easy to edit beside the application while avoiding submodule
friction during the transition to a regular framework dependency. The
`uniquode` Git repository remains rooted at the workspace parent and ignores
the nested `wevra/` checkout, which has its own Git repository.

The workspace parent is a local development coordination layer rather than a
runtime package. It owns the shared `uv.lock` while `wevra/` is a local
workspace member, and it owns the application validation commands. The ignored
`wevra/` checkout is a temporary dependency source only; Wevra remains an
independent repository and owns its own validation.

## Dependency Model

`app` should declare `wevra` as a normal project dependency. Until Wevra is
available as a regular published or pinned dependency, the local workspace root
may resolve `wevra` from the ignored checkout:

```toml
[tool.uv.sources]
app = { workspace = true }
wevra = { workspace = true }

[tool.uv.workspace]
members = [
  "app",
  "wevra",
]
```

`uv` then resolves the application and local Wevra checkout together into one
lock, so shared dependency versions stay aligned while the dependency is
editable. Root validation remains application-focused and should not run
Wevra-owned tests, linting, type checks, or package-build checks.

The application should remove `wevra` from its build backend module list:

```toml
[tool.uv.build-backend]
module-name = ["app"]
```

`app` becomes the application package. `wevra` becomes a dependency.

Member-local lock files should be removed while the parent workspace lock is in
use. Running `uv` from `app` should discover the parent workspace and use the
single root `uv.lock`.

Application test commands should run with `app` as the working directory because
project tools intentionally resolve the host project from `cwd`. The workspace
root may still drive those commands using `uv --directory app ...`.

When Wevra is available as a regular dependency, remove `wevra` from the root
workspace members and sources, stop checking out `wevra/` in this repository's
CI, and keep this repository validating only the application.

## Wevra Project Metadata

The new `wevra` project should be installable on its own, using the same Python
target and compatible tooling:

```toml
[project]
name = "wevra"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
  # framework runtime dependencies currently required by src/wevra
]

[build-system]
requires = ["uv_build>=0.11.18,<0.12.0"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = ["wevra"]
```

Runtime dependencies should move with the framework when they are used by
`wevra` code. Application-only dependencies should stay in `app`.

Expected framework-owned dependencies include, subject to import verification:

- Alembic and SQLAlchemy async support for `wevra.db`;
- Click for `wevra.tools` and `wevra.auth.cli`;
- envex for reusable settings adapters;
- FastAPI/Starlette/Jinja2 for `wevra.web`;
- FastAPI Users and database drivers used by `wevra.auth`.

`dbscripts` is currently a Git dependency used by migration command support; if
the import lives in `wevra`, its source configuration moves to the `wevra`
project.

## Test Ownership

Move tests that assert framework behaviour into `wevra/tests`, including:

- `tests/test_wevra_web.py`;
- `tests/test_wevra_db.py`;
- `tests/test_wevra_auth.py`;
- `tests/test_wevra_namespace.py`;
- reusable portions of `tests/test_validate.py`, `tests/test_identitymgr.py`,
  and `tests/test_app.py` that test `wevra` rather than `uniquode`.

Keep application integration tests in `app`, especially tests proving:

- `app` imports and starts with workspace `wevra`;
- `app.toml` configured modules load `app`, `wevra.web`, and
  `wevra.auth`;
- project scripts still target `wevra.tools.*` and `wevra.auth.cli.identitymgr`;
- application-specific settings, validation adapters, routes, and templates
  remain application-owned.

Avoid duplicating broad test coverage in both repos. The `wevra` project should
own framework correctness; `app` should own integration and application policy.

## Git And GitHub

Implementation should create `wevra` inside the workspace parent from a
history-filtered clone of the current `uniquode` repository rather than from a
fresh copy. Use
`git-filter-repo` to preserve useful framework history while removing
application-only history from the extracted project.

The filtered clone should keep current framework paths and relevant historical
paths, including:

- current `src/wevra/`;
- historical reusable packages such as `src/web_core/`, `src/data_core/`,
  `src/auth_ext/`, and `src/tools/`;
- Wevra-owned tests and framework package documentation needed by the
  standalone framework.

After filtering, clean the extracted repository into a standalone Python
project with `src/wevra`, Wevra-owned tests, its own `pyproject.toml`, and
framework documentation. Then push it to GitHub as the public repository
`Uniquode/wevra`.

Remote setup includes:

- create `wevra` as the filtered clone inside the workspace parent;
- commit the extracted standalone framework project if the filtering cleanup
  leaves local edits;
- create the public `Uniquode/wevra` GitHub repository;
- push the filtered `wevra` repository to GitHub;
- leave `app` depending on the sibling workspace member for now;
- add Wevra-owned GitHub Actions for tests, linting, type checking, package
  build, and CodeQL analysis;
- add Wevra-owned Dependabot and Dependabot auto-merge automation;
- add Wevra-local pre-commit configuration;
- mirror the relevant `uniquode.io` merge settings, branch protection, and
  required-check rules onto `Uniquode/wevra`.

The `uniquode` repository should not vendor `wevra` source after extraction.
The intended local development shape is a tracked `app/` project plus an
ignored nested `wevra/` checkout as sibling directories under the workspace
root. Do not use Git submodules for this workflow.

## OpenSpec Ownership

OpenSpec remains owned by the `uniquode` repository. Do not copy or initialise
OpenSpec artifacts in `wevra`; future Wevra changes are still introduced and
shaped from this application repository while Wevra is being driven by concrete
application requirements.

## Documentation

Both projects should document the local development shape:

```text
wevra must exist beside app inside the local uniquode workspace root.
```

The `app` project should explain that `wevra` is the framework dependency and
that `app/src/app` contains only the application. The workspace README should
explain that the parent `uv.lock` is authoritative for local coordinated
development.

`wevra` should explain its package areas:

- `wevra.core`;
- `wevra.web`;
- `wevra.db`;
- `wevra.tools`;
- `wevra.auth`.

## Scheduling

This extraction should be implemented before `refactor-route-and-view`. The
route/view refactor belongs to `wevra.web`, so it should land in the extracted
framework project rather than being moved shortly after implementation.

## Risks

- Dependency ownership may be wrong on the first pass if imports are not
  checked carefully.
- Tests may temporarily fail if `pythonpath` still points only at the app's
  `src` tree.
- Local workspace dependency means a fresh checkout of `uniquode` requires a
  local `wevra/` checkout under the workspace root until packaged/Git
  dependency handling is introduced.
- Filtered history requires careful path selection because the framework lived
  under temporary package names before `src/wevra`.
- Required GitHub checks can block Wevra PRs if provider checks are not
  installed or reporting. Mitigation: mirror only checks already observed on
  `uniquode.io`, then verify Wevra pull request check rollups after enabling
  the ruleset.

## Open Questions

- Should `app` eventually depend on a Git revision/tag for normal development
  while keeping a workspace override for local framework work?
- Should `identitymgr`, `migrate`, `runserver`, and `validate` script entry
  points remain declared only by `app`, or should the framework project
  also expose its own generic command names for direct framework testing?
