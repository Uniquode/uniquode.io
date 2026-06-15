## Why

Linear: [UT-212](https://linear.app/uniquode/issue/UT-212/add-application-module-composition)

The project is accumulating reusable packages that need to contribute more than
plain Python helpers. Identity is the immediate driver: `auth_ext` should own
its models, route surfaces, default templates, template context, and any
module-owned static assets without being folded into the `uniquode`
application package.

At the same time, applications need to remain explicit about what they are made
from. A public-only application should be able to omit `auth_ext` entirely and
therefore avoid loading identity models, routes, templates, context providers,
or startup wiring. An identity-enabled application should include `auth_ext`
intentionally and retain control over URL placement, product policy, and
overrides while using or replacing the composed `web_core` layout and theme
defaults.

That composition decision should not belong only to the web application runtime.
Alembic, validation, static-asset collection, and future project CLIs need the
same view of configured modules without importing application FastAPI startup
code, runtime-only settings, or identity-specific application state.

## What Changes

- Introduce `app.toml` as the shared, file-backed application composition
  configuration, similar in spirit to Django's `INSTALLED_APPS`, that defines
  the enabled modules, deterministic ordering, and module composition options.
- Allow `APP_CONFIG` to point runtime, Alembic, validation, and future CLIs at a
  non-default composition configuration path.
- Add a small composition configuration loader that runtime settings, Alembic,
  validation, static-asset collection, and future CLIs can consume without
  constructing the FastAPI application, Jinja environment, or `auth_ext`
  runtime state.
- Add top-level `web_core` and `data_core` packages inside the repository as
  application-independent composition layers. `web_core` owns FastAPI,
  Starlette, Jinja, and web resource composition; `data_core` owns SQLAlchemy
  model metadata discovery, shared declarative base support, and Alembic
  migration infrastructure.
- Define optional module surface conventions for:
  - SQLAlchemy model metadata from `<module>.models` when present.
  - Alembic migration version locations from module-owned
    `<module>/migrations/versions/` directories when present.
  - Web routes from `<module>.routes` through a `module_routes` export.
  - Package templates under `<module>/templates`.
  - Package static assets under `<module>/static`.
  - Template-context providers registered from `<module>.context` with
    `add_to_context`.
- Preserve application control over composition:
  - Routes are registered only for configured modules.
  - Relative module route paths are placed under application-configured module
    route prefixes.
  - Absolute `/`-prefixed route paths are honoured as explicit module paths.
  - Route conflicts fail validation/startup rather than relying on ordering.
- Support logical template and static namespaces backed by application override
  roots first, then configured module package sources in deterministic
  precedence order.
- Add a collectstatic-style static export boundary that can examine configured
  application and module static sources, select the winning asset for each
  logical path, and copy those assets into a deployment directory without
  booting the web application. This belongs to `web_core`, not `auth_ext`.
- Add configurable Jinja template reload/cache behaviour so local development
  can edit templates without restarting while production can keep caching.
- Add a generic async template-context provider pipeline. Configured modules
  register static context dictionaries or request-time provider callables from
  `<module>.context`, and the application resolves them in module order at
  startup.
- Move identity route ownership and default identity templates toward
  `auth_ext`, with application override support by logical template path.
- Keep application-specific concerns such as branding, product navigation,
  redirects, delivery, and policy in the host application, while `web_core`
  provides reusable default theme, layout, error, form, and static foundations
  that host applications can omit or override.

## Capabilities

### New Capabilities

- `application-module-composition`: Defines configured module composition,
  optional module surfaces, model metadata loading, route inclusion, route
  prefixing, template/static source precedence, context-provider discovery, and
  composition validation.

### Modified Capabilities

- `web-foundation`: Replace the single physical template/static-root
  assumption with logical namespaces backed by configured module package
  sources.
- `fastapi-users-auth-ext`: Allow `auth_ext` to publish identity route
  surfaces, model metadata, default overrideable identity templates, and
  optional static assets without depending on `uniquode`.
- `identity-authentication`: Move user-facing identity route/template ownership
  from the application to `auth_ext` defaults while preserving application
  control over inclusion, layout/theme, delivery, redirects, policy, and
  overrides.

## Impact

- Affected areas include `app.toml`, `APP_CONFIG`, `web_core`, `data_core`,
  application settings, model metadata loading, migration metadata
  configuration, module-owned migration version locations, route registration,
  template rendering, static asset serving and export, web validation, future
  CLI boundaries, `auth_ext` identity route/template ownership, and identity
  templates under `templates/identity`.
- Existing application routes should continue to work through the new
  composition mechanism, but route registration and resource loading will move
  behind the shared core instead of remaining coupled to the `uniquode`
  application package.
- No new external runtime dependency is expected; `web_core` may depend on
  FastAPI, Starlette, Jinja2, and Python import machinery already present in
  the project, while `data_core` may depend on SQLAlchemy metadata and Alembic
  already present in the project.
