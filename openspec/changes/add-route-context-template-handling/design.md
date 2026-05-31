## Context

The current web foundation is application-centred: `uniquode` registers routes
directly, renders from one filesystem template root, and injects a small fixed
template context from the renderer plus route-local helpers. That worked while
identity pages were host-owned, but it no longer fits the revised package
boundary where `auth_ext` owns identity routes and default `templates/identity`
content.

The new shape needs to stay explicit. Route registration, template precedence,
context providers, CSRF handling, and route ordering are application composition
decisions, so installed packages must not silently mount themselves. At the same
time, reusable modules need a simple way to publish their web surface so an
application can include it without hand-wiring every route and template path.

## Goals / Non-Goals

**Goals:**

- Introduce a small generic web-composition core inside `uniquode`, isolated
  enough that it can later become a reusable `fastapi-web-core` package.
- Let modules publish page routes, partial routes, API routers, package
  templates, and template-context providers through a simple `module_routes`
  convention.
- Let applications explicitly list enabled route modules in settings or
  composition code.
- Preserve a single logical template namespace while allowing multiple physical
  template sources.
- Make application template overrides deterministic: application templates
  always win over enabled module package templates.
- Add an async template-context provider pipeline so domains such as identity,
  theme, billing, or projects can contribute context independently.
- Move default identity route/template ownership to `auth_ext` without making
  `auth_ext` import `uniquode`.
- Keep application-level theme, branding, layout chrome, and navigation in the
  application base templates and application context providers.
- Support development template editing without application restart through
  configurable template reload/cache behaviour.

**Non-Goals:**

- Do not scan installed packages automatically for routes or templates.
- Do not introduce a frontend build pipeline or new runtime dependency.
- Do not move application theme ownership into `auth_ext`.
- Do not make templates the source of authorisation decisions.
- Do not extract an external package in this change; only create a clean
  extraction seam.

## Decisions

### Add An Isolated `uniquode.web_core` Package

Create a generic internal package for web-composition contracts and helpers.
The package should avoid product dependencies and should not import application
settings, product routes, or `auth_ext`.

Initial contents should include contracts such as:

- `HtmlView`
- `HtmlRouteDefinition`
- `ModuleRoutes`
- template source specifications
- template-context provider specifications
- route module loading/resolution helpers
- context provider resolution/merging helpers

Existing `uniquode.web` modules can remain as application adapters while the
generic pieces move into `uniquode.web_core`. This gives a clear future
extraction path without prematurely publishing a separate package.

Alternative considered: keep extending `uniquode.web` directly. That is faster
for the first edit, but it blurs the line between generic web-platform code and
application-owned theme/error/rendering policy.

### Use `module_routes` As The Route Module Export

Each enabled route module should expose a top-level `module_routes` object:

```python
module_routes = ModuleRoutes(
    page_routes=(...),
    partial_routes=(...),
    api_routers=(...),
    template_packages=("auth_ext",),
    context_providers=("auth_ext.context.identity_context",),
)
```

All fields should have empty defaults so applications can back-fill missing
elements and modules only declare what they own.

The application should explicitly configure route modules, for example:

```python
enabled_route_modules = (
    "public.routes",
    "auth_ext.routes",
)
```

The loader imports those modules in order and reads `module_routes`. Missing or
malformed exports should fail at startup with a clear configuration error.

Alternative considered: treat any importable `routes` module as automatic. This
was rejected because route registration has runtime side effects and must remain
host-controlled.

### Keep Route Surfaces Typed And Separate

`ModuleRoutes` should keep page routes, partial routes, and API routers
separate. Page and partial routes bind route metadata to view objects that
render full templates or fragments. API routers remain FastAPI routers and stay
machine-oriented.

This preserves the existing page/partial/API distinction and keeps CSRF/error
handling policies surface-aware.

### Use One Logical Template Namespace With Multiple Physical Sources

Template names remain logical paths such as:

```text
identity/pages/login.html
identity/pages/signup.html
layouts/page.html
components/form_errors.html
```

The renderer should search physical sources in deterministic order:

1. Application template root.
2. Enabled module package template sources in configured order.

Resolution stops at the first match. Jinja caching then handles repeated
lookups according to environment settings.

This lets `auth_ext` ship:

```text
auth_ext/templates/identity/pages/login.html
```

while an application can override it with:

```text
src/templates/identity/pages/login.html
```

Alternative considered: keep all templates in one physical `src/templates`
tree. That prevents publishable modules from owning their default templates and
forces hosts to copy module templates into the application.

### Keep Application Layout And Theme Above Module Templates

Module templates can provide page content, forms, fragments, and module-local
components, but the application owns the outer layout and theme. Identity
templates should extend a stable logical base template such as
`layouts/page.html`; the application provides that template.

Theme context should be contributed by the application context provider and used
by the application base layout. `auth_ext` should not inject or own theme state.

### Resolve Context Providers From Configurable Import Strings

Modules publish context provider names as strings, not already-imported
callables. The application can then append, remove, replace, or reorder provider
names before startup resolution.

At startup, the application resolves each provider string once, validates that
it is an async request callable, and stores callable providers for request-time
execution.

At request time, the dispatcher builds context in layers:

1. Internal reserved context such as `request`, `route_name`, and CSRF fields.
2. Registered provider context dictionaries, called in configured order.
3. View-local context.

Reserved key collisions should fail loudly. Provider key collisions should be
deterministic and either disallowed by default or require an explicit override
policy.

For identity, `auth_ext` should expose a provider that contributes a safe
template user object:

```python
{
    "user": TemplateUser(...) | None,
    "identity": {"authenticated": bool, ...},
}
```

The user object must not expose password hashes, tokens, raw ORM relationships,
or reset/verification internals.

Alternative considered: special-case `current_user` in the renderer. That was
rejected because other modules need the same mechanism and because resolving
identity context is async.

### Make Template Cache And Reload Behaviour Configurable

Template rendering should support development and production defaults:

- local/development: reload enabled, cache disabled or very small
- staging/production: reload disabled, positive cache size

The renderer configuration should expose explicit values so tests and operators
can override environment-derived defaults.

## Risks / Trade-offs

- [Risk] Route modules can still conflict on paths or route names. → Mitigation:
  validate route names, method/path pairs, template references, and API prefixes
  during startup or the existing validation command.
- [Risk] Multiple modules can publish the same logical template path. →
  Mitigation: application root always wins; module precedence follows the
  enabled module order; validation can report duplicate package defaults.
- [Risk] Context providers can create surprising key collisions. → Mitigation:
  reserve internal keys, prefer module/domain root keys, and fail on provider
  collisions unless an explicit override policy is configured.
- [Risk] Moving identity routes into `auth_ext` can accidentally introduce a
  reverse dependency on `uniquode`. → Mitigation: keep generic route/view
  contracts in `uniquode.web_core` during incubation and continue import-boundary
  tests for `auth_ext`.
- [Risk] Package templates that extend application layouts create an implicit
  host contract. → Mitigation: document required logical base templates and keep
  them small/stable.
- [Risk] Development template reload can hide production caching behaviour. →
  Mitigation: test both reload and cached renderer configurations.

## Migration Plan

1. Add the generic `uniquode.web_core` contracts and module route loader while
   keeping current route behaviour intact.
2. Convert existing public and identity route registration to the
   `module_routes` shape.
3. Add template source composition with application-first precedence and move
   current single-root rendering behind that mechanism.
4. Add context-provider registration and move theme context out of identity
   route helpers into an application provider.
5. Move identity routes and default identity templates into `auth_ext`, keeping
   logical template paths stable so application overrides continue to work.
6. Update validation to inspect enabled module routes and template sources.
7. Refresh ADR/spec wording that currently states identity templates are
   application-owned.

Rollback is straightforward while route paths and template names remain stable:
the application can re-enable host-owned identity route registration and remove
`auth_ext.routes` from the enabled module list.

## Open Questions

- What should the exact settings names be for enabled route modules, template
  reload, template cache size, and context provider overrides?
- Should provider key collisions be completely forbidden, or should an explicit
  replacement policy be supported from the start?
- Should duplicate package template paths be warnings in validation or startup
  errors?
- Which safe identity fields belong in the first `user` template object?
