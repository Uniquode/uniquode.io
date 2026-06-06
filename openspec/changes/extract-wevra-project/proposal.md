## Why

`wevra` has grown from an internal namespace into the reusable framework layer
for web, data, tooling, and auth infrastructure. Keeping it physically inside
the `uniquode` application repo weakens the boundary while major framework
design changes are still happening, especially the upcoming route/view
refactor.

Extracting `wevra` into its own adjacent editable project now will make the
framework boundary real without slowing local development.

## What Changes

- Create a separate `wevra` Python project adjacent to this checkout, intended
  to live at `../wevra` during local development.
- Move the full `src/wevra/` package and Wevra-owned tests into the new project.
- Give the new project its own `pyproject.toml`, package metadata, README,
  validation configuration, and Git repository.
- Push the new project to GitHub as its own repository.
- Update `uniquode` to depend on `wevra` through an editable local path source:
  `wevra = { path = "../wevra", editable = true }`.
- Remove `wevra` from the `uniquode` build package list so the application
  package no longer ships framework source.
- Keep `uniquode` integration tests proving the application works against the
  editable `wevra` dependency.
- Schedule this extraction before implementing `refactor-route-and-view` so new
  framework design work lands in the framework project.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `application-infrastructure`: Split reusable `wevra` framework code into an
  adjacent editable project and consume it from `uniquode` as an explicit
  dependency.

## Impact

- Affected code and metadata include `src/wevra/`, Wevra-owned tests,
  `pyproject.toml`, `uv.lock`, README documentation, validation commands,
  OpenSpec live references, and Git/GitHub project setup.
- Local development requires the sibling `../wevra` checkout.
- CI is intentionally out of scope for now; no CI wiring is required by this
  change.
- No runtime behaviour should change after `uniquode` is installed with the
  editable `wevra` dependency.
