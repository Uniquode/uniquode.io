## Why

`wevra` has grown from an internal namespace into the reusable framework layer
for web, data, tooling, and auth infrastructure. Keeping it physically inside
the `uniquode` application repo weakens the boundary while major framework
design changes are still happening, especially the upcoming route/view
refactor.

Extracting `wevra` into its own adjacent workspace project now will make the
framework boundary real without slowing local development.

## What Changes

- Create a separate `wevra` Python project beside `app` inside the local
  `uniquode` parent.
- Move the full `src/wevra/` package and Wevra-owned tests into the new project.
- Give the new project its own `pyproject.toml`, package metadata, README,
  validation configuration, and Git repository.
- Push the new project to GitHub as its own repository.
- Update `app` to depend on `wevra` through the parent `uv` workspace,
  with both projects resolved from one shared root `uv.lock`.
- Remove `wevra` from the application build package list so the application
  package no longer ships framework source.
- Keep `app` integration tests proving the application works against the
  adjacent workspace `wevra` dependency.
- Schedule this extraction before implementing `refactor-route-and-view` so new
  framework design work lands in the framework project.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `application-infrastructure`: Split reusable `wevra` framework code into an
  adjacent workspace project and consume it from `app` as an explicit
  dependency.

## Impact

- Affected code and metadata include `src/wevra/`, Wevra-owned tests,
  `pyproject.toml`, `uv.lock`, README documentation, validation commands,
  OpenSpec live references, and Git/GitHub project setup.
- Local development requires the sibling `wevra` checkout inside the
  `uniquode` parent.
- Wevra repository automation is included after explicit follow-up request:
  Wevra owns its GitHub Actions, CodeQL, Dependabot, Dependabot auto-merge,
  pre-commit configuration, branch protection, and required-check rules.
- The application repository's existing CI/pre-commit checks remain
  app-focused and do not run Wevra-owned tests, linting, type checks, or
  package-build checks.
- No runtime behaviour should change after `app` is installed with the
  workspace `wevra` dependency.
