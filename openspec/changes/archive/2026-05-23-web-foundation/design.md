## Context

The project has already decided its UI direction at ADR level, but the repository still only contains the ASGI shell and runtime command baseline. There is no application-wide template root, no static asset root, no rendering helper, no route-surface convention beyond the health endpoint, and no validation surface for web-structure errors before runtime.

This change needs to establish the first durable web foundation without overreaching into user management, content management, or a front-end build pipeline. It must align with ADR 0003 and ADR 0004, preserve the async-first FastAPI platform, and keep the implementation simple enough that later user, admin, and public-page work can build on it incrementally.

## Goals / Non-Goals

**Goals:**

- Establish configurable global template and static roots, with defaults at `src/templates/` and `src/static/`, plus a configurable static route prefix with a default of `/static/`, as required by ADR 0004.
- Introduce the first template hierarchy, shared component conventions, and rendering helper for server-rendered HTML.
- Establish the baseline page, partial, and API route boundaries, the route naming conventions needed for later reverse resolution and export, and the first HTML dispatcher protocol under FastAPI.
- Provide the initial Pico CSS and `htmx` delivery approach for MVP without introducing a front-end build pipeline.
- Ensure theme handling is expressed semantically across the shared template and stylesheet foundation so later templates inherit light and dark behaviour without hard-coded per-template colour logic.
- Introduce a first validation surface for template, route, and static-asset structure that can grow into the generic CLI ADR 0004 expects.

**Non-Goals:**

- Implement identity, authorisation, or administrative workflows.
- Introduce a CMS or content-managed public-page model.
- Introduce TypeScript, npm, Sass/SCSS, or another front-end asset pipeline.
- Implement a complete route-manifest export format.
- Finalise every future validation rule; this change only needs the first extensible foundation.

## Decisions

### 1. Use configurable global template and static roots outside `src/uniquode`

Templates will default to `src/templates/` and static assets will default to `src/static/`, but both locations should be supplied through project settings rather than hard-coded into the rendering or static-asset implementation. Static assets should also be exposed through a configurable route prefix that defaults to `/static/`. `src/uniquode/` remains the core application package for app construction, settings, route glue, and shared infrastructure rather than becoming a container for all UI resources. The first concrete site-facing feature module should be able to live in a sibling package such as `src/site/`.

This follows ADR 0004 directly and keeps the core package distinct from feature assets. The main alternative was keeping templates and static files under `src/uniquode/`, but that would blur the separation between core infrastructure and feature resources and make later sibling feature modules less natural. Another alternative was hard-coding the global roots in the rendering layer; that would reduce flexibility for tests, packaging, or future deployment adjustments without adding meaningful simplicity.

### 2. Introduce a minimal rendering layer rather than rendering directly in route handlers

The web layer should expose a small rendering helper that knows the template root, renders templates by root-relative path, and provides the basis for consistent page, partial, and error rendering. It should support template context assembly through ordinary Python dictionaries and remain simple enough to extend later.

The alternative was calling the templating environment directly in each handler. That would work for a tiny app, but it would scatter template-environment knowledge and make later context composition, error rendering, and validation harder to unify.

### 3. Use an internal HTML dispatcher and declarative view registry under FastAPI

The HTML site layer should use a request-dispatch protocol under FastAPI rather than relying only on one decorator-bound function per page. Page-oriented views should register declaratively through route definition modules in the same spirit as Django `urls.py`, while still using the project's own registry and matching logic. Registered views should expose a small protocol with selection and serving behaviour so the application can inspect the incoming request, select the final view deterministically, and then delegate response generation to that view.

FastAPI should still own the outer ASGI routing layer. Explicit FastAPI routes remain the right approach for operational endpoints and machine-oriented `/api/...` routes. The dispatcher should be used for the HTML page and partial layer, not for every request in the system.

The alternative was relying entirely on ordinary decorated page routes. That would work, but it would make the planned view registry, reverse resolution model, and later validation surface less coherent. The opposite extreme, routing every request in the application through the dispatcher, would be too opaque and would give up too much of FastAPI's strengths for APIs and operational routes.

### 4. Keep static asset serving separate from HTML dispatch

Static assets should not participate in the HTML handler-selection flow. The application should define a configurable static filesystem root and a configurable static URL prefix, with app-served static delivery available for development and validation. The same URL contract should remain valid when production infrastructure such as Nginx serves `/static/...` directly.

The alternative was treating static files as just another handler in the dispatcher. That would blur concerns, complicate matching logic, and work against the likely production goal of offloading static byte serving.

### 5. Keep route surfaces explicit and separate

The initial web layer should keep full-page HTML routes, HTML partial routes, and machine-oriented API routes as separate route surfaces. The first implementation does not need a complete API surface, but the route-registration pattern should leave space for page, partial, and `/api/<module>/...` registration without mixing concerns. For site-facing HTML work, `src/site/routes.py` and `src/site/views.py` should be the first concrete pattern to prove the design.

The alternative was one flat route set with ad hoc template or JSON responses. That would be faster initially, but it would make later policy binding, reverse resolution, testing, and validation messier.

### 6. Deliver Pico CSS and `htmx` without a build pipeline

For MVP, Pico CSS and `htmx` should be delivered without npm or another build chain. Pico may be consumed through a CDN-backed stylesheet reference, and `htmx` may be delivered in the same lightweight way. Project-specific CSS should be layered separately under the static root.

The alternative was introducing npm, TypeScript, or Sass/SCSS immediately. That would add build and tooling complexity before the project has concrete requirements for it.

### 7. Express theme behaviour through semantic styling roles

The first web foundation should not treat theme support as a small toggle that only sets `data-theme` on the document root. Shared templates and project CSS should be organised around semantic styling roles such as page background, surface, text, muted text, border, and accent so later page work can inherit theme behaviour naturally. Mode changes between `auto`, `light`, and `dark` should primarily change token values and inherited styles rather than requiring template-local light or dark colour choices.

The alternative is keeping light-looking colours embedded directly in the first stylesheet and treating mode support as something to refine later. That would make early templates visually misleading, encourage hard-coded colour usage in feature work, and turn foundational theming into a retrofit rather than a baseline rule.

### 8. Start the validation surface as a project CLI

The first validation step should be a project CLI or command surface that inspects the configured route and template structures and reports obvious broken references before the server is run. The first version only needs to validate the implemented web foundation, but the shape should be extensible toward broader route, template, static-asset, and `htmx` checks later.

The alternative was relying entirely on runtime testing. That would discover some problems, but not as early or as systematically as a dedicated validation surface.

## Risks / Trade-offs

- `Relative template composition semantics may conflict with Jinja defaults` → Keep the first helper conservative and document where root-relative and local composition rules apply; only add custom loader behaviour where it is clearly needed.
- `Early validation may overfit the initial structure` → Keep the first CLI intentionally narrow and grow checks only when the implementation creates a real need.
- `CDN delivery adds an external dependency for front-end assets` → Limit this to MVP convenience and keep the static layout ready for vendoring later if policy or reliability requirements change.
- `Adding a rendering helper introduces a thin abstraction layer` → Keep it small, testable, and focused on environment setup and consistent rendering rather than inventing a framework.

## Migration Plan

1. Add the default template and static roots, expose them and the static route prefix through settings, and wire them into the application.
2. Introduce the rendering helper, HTML dispatcher protocol, declarative view registry, base templates, shared component locations, and baseline static stylesheet structure.
3. Add semantic theme tokens and ensure the shared templates consume them rather than relying on hard-coded light-mode assumptions.
4. Add the first page and partial routes using the new conventions, plus separate static mounting for development.
5. Add the first validation command and focused tests for dispatcher behaviour, rendering, route wiring, static asset configuration, and validation behaviour.

No production data migration is required for this change. Rollback is low risk because the current application has no user-facing HTML surface yet.

## Open Questions

- Whether the first implementation should vendor Pico and `htmx` immediately despite the ADR-level CDN decision for MVP.
- How much local template-composition behaviour should be implemented in the first rendering helper versus left to explicit root-relative references.
- What minimum semantic token set should be mandatory in the first shared stylesheet layer.
- Which initial validation checks deliver the best value without turning the first CLI into a mini framework.
