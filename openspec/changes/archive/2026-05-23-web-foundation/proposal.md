## Why

The project has settled the core UI direction in ADR 0003 and ADR 0004, but the repository still lacks the concrete web foundation needed to build pages consistently. The next change should establish the first template, static asset, styling, routing, and validation conventions so later user, admin, and public-page work can build on a stable baseline.

## What Changes

- Establish the first server-rendered web foundation for templates, layouts, shared components, static assets, and page rendering.
- Introduce the initial Pico CSS and `htmx` delivery conventions needed by the HTML-first UI architecture.
- Define route naming, page/partial/API route boundaries, an internal HTML request-dispatch and view-registration model under FastAPI, and the first render helper and validation CLI expectations.
- Update the application infrastructure contract to reflect configurable global template and static roots, a configurable static route prefix with a default of `/static/`, explicit separation between HTML dispatch and static asset serving, and the feature-module layout that ADR 0004 now requires.

## Capabilities

### New Capabilities
- `html-ui-foundation`: Defines the baseline HTML-first UI foundation, including template hierarchy, shared components, static asset delivery, styling entry points, route surface conventions, and pre-runtime web-structure validation expectations.
  This includes an internal request-dispatch model and declarative view registration for the HTML web layer.

### Modified Capabilities
- `application-infrastructure`: Update the project layout and infrastructure requirements to reflect configurable template and static roots, a configurable static route prefix, separate static asset serving from HTML dispatch, feature-module structure beside `src/uniquode`, and the foundational rendering and validation hooks required by the web layer.

## Impact

- Affected code: application factory and route registration, template rendering support, static asset configuration, and project layout under `src/`.
- Affected dependencies: likely addition of `htmx` and Pico CSS delivery support without introducing a front-end build pipeline.
- Affected validation/tooling: tests for rendering and route wiring, plus an initial web-structure validation command or CLI surface.
- Affected specs: new `html-ui-foundation` capability and a delta to `application-infrastructure`.
