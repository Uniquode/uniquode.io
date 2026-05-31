## Why

Reusable modules now need to publish coherent web surfaces without being folded
into the `uniquode` application package. Identity is the immediate driver:
`auth_ext` should own its identity routes and default `templates/identity`
content, while the application keeps control of layout, theme, route inclusion,
and overrides.

## What Changes

- Add a small, isolated web-composition core inside `uniquode` for now, with a
  shape that can later be separated into a reusable `fastapi-web-core` style
  package.
- Define a simple module export convention, such as `module_routes`, for route
  modules to publish page routes, partial routes, API routers, template package
  locations, and template-context provider names.
- Add explicit application settings/configuration for enabled route modules so
  module web surfaces are discovered deterministically rather than through
  implicit package scanning.
- Preserve route-surface separation: page and partial routes point to views that
  render templates/fragments, while API routers remain machine-oriented.
- Support a single logical template namespace backed by multiple physical
  sources: application templates first, then enabled module package templates in
  configured order.
- Allow application defaults to back-fill missing module elements, including
  template roots, template-context providers, and other web-composition hooks.
- Add configurable Jinja template reload/cache behaviour so local development can
  edit templates without restarting the application while production can retain
  caching.
- Add a generic async template-context provider pipeline. Modules publish
  provider import strings; the application can append, remove, or override the
  configured provider list before callables are resolved at startup.
- Move identity route ownership and default identity templates toward `auth_ext`,
  with application override support by logical template path.
- Keep application-level concerns such as theme, branding, layout chrome, and
  product navigation in the application base templates and application context
  providers.

## Capabilities

### New Capabilities

- `module-web-composition`: Defines the module route/context/template composition
  core, including `module_routes`, enabled route modules, route-surface
  registration, package template sources, context-provider discovery, and
  template cache/reload settings.

### Modified Capabilities

- `html-ui-foundation`: Replace the single physical template-root assumption
  with a single logical template namespace backed by application and enabled
  module template sources, and define how page/partial/API routes are composed
  from enabled modules.
- `fastapi-users-auth-ext`: Allow `auth_ext` to publish identity route surfaces
  and default overrideable identity templates without depending on `uniquode`.
- `identity-authentication`: Move user-facing identity route/template ownership
  from the application to `auth_ext` defaults while preserving application
  control over inclusion, layout/theme, delivery, redirects, policy, and
  overrides.

## Impact

- Affected areas include `uniquode.web` dispatcher/rendering code,
  application settings, route registration, web validation, `auth_ext` identity
  route/template ownership, and identity templates under `templates/identity`.
- Existing application routes should continue to work through the new
  composition mechanism, but route registration and template loading will move
  behind the shared web-composition core.
- No new runtime dependency is expected; this should use FastAPI, Starlette,
  Jinja2, and Python import machinery already present in the project.
