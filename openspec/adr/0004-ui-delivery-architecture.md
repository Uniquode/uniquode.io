# 0004: UI Delivery Architecture

Date: 2026-05-20

Status: Provisional

## Context

ADR 0001 established FastAPI/Starlette as the application platform and selected Jinja2 for server-rendered templates by default unless a later decision required a richer client application.

The project now needs a more explicit front-end delivery model so routing, templates, access control, and future API design remain coherent.

The application must support:

- public pages;
- authenticated user pages;
- administrative surfaces secured by session-backed authentication and authorisation;
- progressively enhanced interactions where dynamic updates improve usability without forcing a heavy client-side application.

The team prefers not to introduce a heavy JavaScript front end unless product requirements justify the additional build, deployment, testing, and routing complexity.

The application should still expose an API surface, and dynamic UI behaviour should be able to reuse shared application services rather than creating a split architecture.

The project also needs clear conventions for where templates and static assets live, how feature modules integrate with the core application, and how route and template structures can be validated before runtime.

## Decision

Use a server-rendered HTML-first UI architecture.

Use Jinja2 templates as the primary UI rendering mechanism for full-page responses.

Use `htmx` as the preferred dynamic enhancement layer where partial page updates, inline actions, or progressively enhanced workflows improve the interface. `htmx` is expected to be used in the initial web-foundation slice, but baseline page and form flows must still work as ordinary HTML interactions without depending on `htmx`.

Use configured module package template sources such as:

```text
src/web_core/templates/
src/public/templates/
src/auth_ext/templates/
```

Use configured module package static sources such as:

```text
src/web_core/static/
src/auth_ext/static/
```

Treat `src/uniquode/` as the core host application package rather than the
home for reusable web foundation code, feature modules, templates, or static
assets.

Allow feature modules such as `auth_ext`, `api`, `integrations`, and others to
live alongside `uniquode` when required. Feature modules should integrate with
the core application through configured module surfaces rather than by being
folded into the core package.

Allow configured modules to own templates and static assets inside their package
directories. Resources are addressed by stable logical paths, and later
configured modules may override earlier module defaults by providing the same
logical path.

Keep HTML page routes, HTML partial routes, and machine-oriented API routes as distinct route surfaces:

- page routes render full templates;
- partial routes return fragment responses intended for `htmx` or similar dynamic enhancement;
- API routes live under `/api/` and return machine-oriented representations.

Prefer module-oriented API paths under `/api/<module>/...` where that keeps API surfaces coherent, while still allowing simpler public or application routes where module-prefixed paths would be unnatural.

Do not introduce a separate JavaScript front-end application as the primary UI architecture at this stage.

Keep routes defined in code rather than in JSON, YAML, or the database. Route metadata may be exported for management, documentation, or tooling use, but exported metadata is not the runtime source of truth.

Use stable route names or identifiers for route generation, management visibility, access-policy binding, and exported route manifests.

Keep slugs in the relevant domain model or content model rather than treating slugs as the primary identity of the routing system itself.

The rendering system must support a coherent template hierarchy, including a ubiquitous base page template, a base HTML error template, and additional top-level archetype base templates where major page classes need them.

Reusable server-rendered components should be composed through partials, includes, macros, or similar template composition patterns rather than through a separate client-side component framework.

Template rendering should use the composed logical template namespace and target
templates by logical path. The implementation should also support local template
composition so includes and related templates can be resolved coherently
relative to the source template where that convention is used.

No front-end asset build pipeline is required initially. Avoid introducing Sass or SCSS compilation unless a later requirement justifies it.

For MVP delivery, consume Pico CSS through a CDN rather than introducing an npm-style front-end asset workflow.

Route naming, reverse resolution, and structural validation of routes, templates, and static assets are first-class concerns. The project should provide a generic validation CLI that reads project configuration, builds the relevant internal structures, and reports broken references or structural errors before runtime where practical.

## Conventions

Shared reusable server-rendered components should live under the logical
template path:

```text
components/
```

Feature modules may also define module-local reusable components under logical
subpaths such as:

```text
<module-base>/components/
```

Use the global component path for components intended to be shared across multiple modules or page types. Use module-local component paths where reuse is primarily internal to one feature area.

Implement components through ordinary Jinja composition patterns such as includes, partials, and macros rather than through a separate component runtime or front-end framework abstraction.

## Consequences

The project keeps its initial delivery model aligned with ADR 0001 and avoids introducing an immediate front-end build pipeline.

The application can ship public pages, authenticated pages, and administrative workflows with one rendering stack and one deployment surface.

`htmx` allows targeted interactivity without forcing the project into SPA routing, state management, or an API-only browser contract.

Using a composed logical template/static namespace keeps resource lookup stable
while allowing feature-oriented ownership through module package sources.

Keeping feature modules alongside the core package avoids turning `uniquode` into an undifferentiated container for every application concern.

Keeping routes in code preserves FastAPI's strengths around typed handlers, explicit path definitions, dependency injection, access control integration, named URL generation, and testability.

An exported route manifest can still support management and operational visibility without shifting execution authority away from the application code.

Keeping `/api/` as a distinct machine-oriented namespace allows the project to add API consumers later while keeping the HTML UI as the primary user experience.

Avoiding an initial asset build pipeline keeps the first web slice lighter, but means template and static conventions must be deliberate enough to support growth without relying on a front-end toolchain to impose structure.

Adding a purpose-built validation CLI increases early implementation work, but reduces the risk of shipping broken routes, template references, static references, or `htmx` structures that are only discovered through runtime failures.

## Open Questions

- Whether public content pages require a content-managed data model in the first release or can begin as code-defined pages with template-backed content.
- What exact rendering helper or abstraction should own template-root resolution, template rendering, and local template composition semantics.
- What exact validation checks should be implemented in the first version of the generic web-structure validation CLI.

## Follow-Up Work

- Define template, layout, and static asset conventions.
- Define the route naming and reverse-resolution conventions.
- Define page, partial, and API route registration patterns.
- Define public-page and protected-page conventions.
- Define the initial template-rendering helper and web-structure validation CLI.
