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

Use adjacent sibling repositories:

```text
/Users/davidn/Code/
  uniquode/
    pyproject.toml
    src/uniquode/
    tests/
  wevra/
    pyproject.toml
    src/wevra/
    tests/
```

This keeps `wevra` easy to edit beside the application while avoiding nested
Git repository and submodule friction.

## Dependency Model

`uniquode` should declare `wevra` as a normal project dependency and use
`tool.uv.sources` for local editable development:

```toml
[project]
dependencies = [
  "wevra",
  # other application/runtime dependencies
]

[tool.uv.sources]
wevra = { path = "../wevra", editable = true }
```

`uv` then installs the sibling project in editable mode, so changes under
`../wevra/src/wevra` are visible to `uv run ...` from the application checkout.
The lock file should capture the local source.

The application should remove `wevra` from its build backend module list:

```toml
[tool.uv.build-backend]
module-name = ["uniquode"]
```

`uniquode` remains the application package. `wevra` becomes a dependency.

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
`wevra` code. Application-only dependencies should stay in `uniquode`.

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

Move tests that assert framework behaviour into `../wevra/tests`, including:

- `tests/test_wevra_web.py`;
- `tests/test_wevra_db.py`;
- `tests/test_wevra_auth.py`;
- `tests/test_wevra_namespace.py`;
- reusable portions of `tests/test_validate.py`, `tests/test_identitymgr.py`,
  and `tests/test_app.py` that test `wevra` rather than `uniquode`.

Keep application integration tests in `uniquode`, especially tests proving:

- `uniquode` imports and starts with editable `wevra`;
- `app.toml` configured modules load `uniquode`, `wevra.web`, and
  `wevra.auth`;
- project scripts still target `wevra.tools.*` and `wevra.auth.cli.identitymgr`;
- application-specific settings, validation adapters, routes, and templates
  remain application-owned.

Avoid duplicating broad test coverage in both repos. The `wevra` project should
own framework correctness; `uniquode` should own integration and application
policy.

## Git And GitHub

Implementation should create `../wevra` as a new Git repository and push it to
GitHub. Because CI is not being introduced yet, the minimum remote setup is:

- initialise Git in `../wevra`;
- commit the extracted framework project;
- create/push the GitHub repository;
- leave `uniquode` depending on the editable sibling path for now.

The `uniquode` repository should not vendor `wevra` source after extraction.
Do not use a nested raw Git checkout inside `uniquode`; the intended local
development shape is adjacent sibling repos.

## Documentation

Both projects should document the local development shape:

```text
../wevra must exist beside ../uniquode for editable local development.
```

`uniquode` should explain that `wevra` is the framework dependency and that
`src/uniquode` contains only the application.

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
- Local path dependency means a fresh checkout of `uniquode` requires a sibling
  `wevra` checkout until packaged/Git dependency handling is introduced.
- Moving history is coarse because the framework files are currently uncommitted
  in the namespace extraction branch; implementation should favour correctness
  over perfect file-history preservation.

## Open Questions

- Should the first GitHub repository be public or private?
- Should `uniquode` eventually depend on a Git revision/tag for normal
  development while keeping an editable override for local framework work?
- Should `identitymgr`, `migrate`, `runserver`, and `validate` script entry
  points remain declared only by `uniquode`, or should the framework project
  also expose its own generic command names for direct framework testing?
