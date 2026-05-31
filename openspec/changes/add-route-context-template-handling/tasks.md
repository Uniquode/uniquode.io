## 1. Web Core Contracts

- [ ] 1.1 Create an isolated `uniquode.web_core` package for generic route,
  template, and context composition contracts.
- [ ] 1.2 Move or mirror `HtmlView` and `HtmlRouteDefinition` into the web core
  without introducing imports from product routes, application settings, or
  `auth_ext`.
- [ ] 1.3 Add a `ModuleRoutes` dataclass with page route, partial route, API
  router, template package, and context provider collections that default to
  empty tuples.
- [ ] 1.4 Add route module loading helpers that import explicit module names,
  read `module_routes`, preserve configured order, and fail clearly on missing
  or malformed modules.

## 2. Application Composition Settings

- [ ] 2.1 Add application settings for enabled route modules with defaults that
  preserve the existing public and identity route surface.
- [ ] 2.2 Add template reload and cache-size settings with local-development and
  non-local deployment defaults.
- [ ] 2.3 Add context provider override settings or application composition hooks
  that allow provider import names to be appended, removed, replaced, or
  reordered before startup resolution.
- [ ] 2.4 Update application startup to load enabled module routes before route
  registration, template renderer construction, and context provider resolution.

## 3. Template Source Composition

- [ ] 3.1 Replace the renderer's single filesystem loader with an
  application-first logical template loader that searches the application
  template root before enabled module package templates.
- [ ] 3.2 Resolve module template package declarations into Jinja package
  template sources without exposing Jinja loader objects as the public module
  contract.
- [ ] 3.3 Preserve stable logical template paths so application overrides use the
  same path as package defaults.
- [ ] 3.4 Apply configurable Jinja `auto_reload` and `cache_size` settings and
  cover both reload-friendly and cached configurations in tests.

## 4. Template Context Providers

- [ ] 4.1 Add a template context provider registry that resolves provider import
  strings to async request callables once at startup.
- [ ] 4.2 Merge provider context dictionaries in configured order before
  view-local context is rendered.
- [ ] 4.3 Protect reserved renderer context keys such as `request`, `route_name`,
  and CSRF fields from provider or view overrides.
- [ ] 4.4 Move application theme context into an application-owned context
  provider rather than identity route helpers.
- [ ] 4.5 Add an `auth_ext` identity context provider that exposes `user` as a
  safe template view object or `None`, plus non-sensitive identity state.

## 5. Route Module Conversion

- [ ] 5.1 Convert existing public route registration to publish `module_routes`
  while preserving current paths, route names, and behaviour.
- [ ] 5.2 Convert current identity route registration to the module route shape
  before moving ownership to `auth_ext`.
- [ ] 5.3 Update the application route registration layer to register page,
  partial, and API routes from loaded module routes in configured order.
- [ ] 5.4 Keep CSRF validation, page/partial surface checks, and API router
  inclusion behaviour equivalent to the current implementation.

## 6. Auth Extension Ownership

- [ ] 6.1 Move reusable identity views and route definitions from
  `uniquode.routes.identity` into `auth_ext` without adding any `auth_ext`
  import from `uniquode`.
- [ ] 6.2 Move default identity templates into the `auth_ext` package under a
  package template source while keeping logical paths under `identity/`.
- [ ] 6.3 Ensure application templates can override every `auth_ext` identity
  template by providing the same logical path in the application template root.
- [ ] 6.4 Ensure `auth_ext` identity templates rely on application-owned base
  layout and theme context rather than owning product shell or theme state.
- [ ] 6.5 Update package metadata so `auth_ext` package templates are included
  when the project/package is built.

## 7. Validation, Tests, And Documentation

- [ ] 7.1 Extend web validation to inspect enabled route modules, `module_routes`
  exports, route conflicts, package template sources, template references, and
  context provider import names.
- [ ] 7.2 Add tests for explicit module inclusion, unlisted module exclusion,
  missing/malformed module errors, and deterministic route registration order.
- [ ] 7.3 Add tests for application-first template override precedence and
  module-to-module package template precedence.
- [ ] 7.4 Add tests for context provider resolution, async context merging,
  reserved-key collision failures, and safe identity `user` context.
- [ ] 7.5 Add tests proving existing login, signup, logout, account,
  password-reset, and verification pages continue to work through `auth_ext`
  route ownership.
- [ ] 7.6 Update README and web validation documentation to describe enabled
  route modules, logical template paths, application overrides, context
  providers, and development template reload settings.
- [ ] 7.7 Refresh ADR/spec wording that still says identity templates are
  application-owned.
- [ ] 7.8 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate add-route-context-template-handling --strict`.
