## 1. `web_ext` Core Layer

- [ ] 1.1 Create a top-level `web_ext` package for shared composition
  configuration, installed-module loading, route/resource/context contracts,
  and static export services.
- [ ] 1.2 Move or mirror `HtmlView` and `HtmlRouteDefinition` into the core
  layer without introducing imports from product routes, application settings,
  `auth_ext`, or application FastAPI startup.
- [ ] 1.3 Add `ModuleRoutes` and module surface contracts for optional page
  routes, partial routes, API routers, model metadata, package templates,
  package static assets, and context provider import names.
- [ ] 1.4 Add installed module loading helpers that import explicit module
  names, preserve configured order, and fail clearly on missing modules.
- [ ] 1.5 Add import-boundary tests proving `web_ext` does not import the
  `uniquode` application package, `auth_ext`, product settings, route modules,
  or deployment secrets.
- [ ] 1.6 Allow `web_ext` to depend on FastAPI and Starlette engine APIs while
  keeping it independent from a concrete application instance.
- [ ] 1.7 Keep application-facing adapters thin so the current `uniquode` app can
  consume `web_ext` without an external package extraction in this change.

## 2. Shared Composition Configuration

- [ ] 2.1 Add an `app.toml` composition configuration schema and loader with
  `installed_modules` defaults that preserve the current public and
  identity-enabled application surface.
- [ ] 2.2 Add composition options for per-module route prefixes, application
  template/static override roots, template reload/cache behaviour, context
  provider overrides, and static export defaults.
- [ ] 2.3 Add `APP_CONFIG` support so runtime startup, Alembic, validation,
  static export, and future CLIs can use an explicit non-default config path.
- [ ] 2.4 Keep the composition loader CLI-safe by avoiding application FastAPI
  startup, Jinja environment construction, route module, `auth_ext`, and
  runtime-secret imports.
- [ ] 2.5 Adapt runtime settings to consume the shared composition
  configuration rather than owning a separate installed-module source of truth.
- [ ] 2.6 Adapt Alembic and migration metadata loading to consume the shared
  composition loader rather than duplicating installed-module defaults.
- [ ] 2.7 Preserve the default `auth.toml` configuration path while allowing
  `app.toml` to reserve compatible auth directives for a separate future
  configuration-unification change.
- [ ] 2.8 Add tests for default `app.toml` loading, `APP_CONFIG` override,
  configured ordering, malformed configuration, missing configured modules, and
  CLI-safe imports.
- [ ] 2.9 Document the `app.toml` location, `APP_CONFIG` override mechanism,
  schema, future auth-directive compatibility, and distinction from deployment
  secrets or product policy settings.

## 3. Module Surface Discovery

- [ ] 3.1 Add surface discovery helpers for conventional model, route,
  template, static, and context-provider surfaces.
- [ ] 3.2 Ensure missing optional surfaces are treated as empty contributions.
- [ ] 3.3 Ensure malformed present surfaces fail clearly before partial
  application registration.
- [ ] 3.4 Ensure template and static package sources are discoverable from
  installed modules without importing route modules.

## 4. Model Metadata Composition

- [ ] 4.1 Adapt migration metadata loading to derive model metadata from
  installed modules with conventional model surfaces.
- [ ] 4.2 Skip installed modules without model surfaces while preserving clear
  errors for malformed model metadata.
- [ ] 4.3 Preserve existing migration metadata ordering and current identity
  table definitions with the default installed module list.
- [ ] 4.4 Add tests proving a public-only installed module list can omit
  `auth_ext` model metadata.
- [ ] 4.5 Add tests proving Alembic can load composed metadata without importing
  runtime application startup.

## 5. Route Composition

- [ ] 5.1 Add route module loading helpers that read `module_routes` from
  installed module route surfaces and fail clearly on malformed exports.
- [ ] 5.2 Apply configured module route prefixes to relative paths while
  preserving absolute `/`-prefixed route paths.
- [ ] 5.3 Convert existing public route registration to publish `module_routes`
  while preserving current paths, route names, and behaviour.
- [ ] 5.4 Convert current identity route registration to the module route shape
  before moving ownership to `auth_ext`.
- [ ] 5.5 Update the application route registration layer to register page,
  partial, and API routes from installed modules in configured order.
- [ ] 5.6 Keep CSRF validation, page/partial surface checks, and API router
  inclusion behaviour equivalent to the current implementation.
- [ ] 5.7 Add tests for relative route prefixing, absolute route paths, route
  name conflicts, and method/path conflicts.

## 6. Template Source Composition

- [ ] 6.1 Replace the renderer's single filesystem loader with an
  application-first logical template loader that searches the application
  template root before installed module package templates.
- [ ] 6.2 Resolve module template package declarations into Jinja package
  template sources without exposing Jinja loader objects as the public module
  contract.
- [ ] 6.3 Preserve stable logical template paths so application overrides use
  the same path as package defaults.
- [ ] 6.4 Apply configurable Jinja `auto_reload` and `cache_size` settings and
  cover both reload-friendly and cached configurations in tests.
- [ ] 6.5 Add tests for application-first template override precedence,
  module-to-module package template precedence, and missing-template behaviour.

## 7. Static Asset Serving And Export

- [ ] 7.1 Replace single-root static serving with an application-first logical
  static asset resolver that searches the application static root before
  installed module package static sources.
- [ ] 7.2 Preserve stable logical static paths so application overrides use the
  same path as package defaults.
- [ ] 7.3 Add a collectstatic-style static export service that writes the
  composed logical static namespace into a configured output directory from
  `web_ext`.
- [ ] 7.4 Ensure static export uses the same precedence rules as runtime static
  serving and writes only the winning asset for each logical path.
- [ ] 7.5 Ensure static export can run from the shared composition loader without
  importing application FastAPI startup, route modules, the Jinja environment, or
  identity-specific runtime state.
- [ ] 7.6 Add tests for static serving precedence, static export precedence,
  duplicate module defaults, application overrides, and missing assets.

## 8. Template Context Providers

- [ ] 8.1 Add a template context provider registry that resolves provider import
  strings to async request callables once at startup.
- [ ] 8.2 Merge provider context dictionaries in configured order before
  view-local context is rendered.
- [ ] 8.3 Protect reserved renderer context keys such as `request`,
  `route_name`, and CSRF fields from provider or view overrides.
- [ ] 8.4 Fail on provider key collisions by default unless an explicit
  override policy is configured.
- [ ] 8.5 Move application theme context into an application-owned context
  provider rather than identity route helpers.
- [ ] 8.6 Add an `auth_ext` identity context provider that exposes `user` as a
  safe template view object or `None`, plus non-sensitive identity state.

## 9. Auth Extension Ownership And Optional Inclusion

- [ ] 9.1 Move reusable identity views and route definitions from
  `uniquode.routes.identity` into `auth_ext` without adding any `auth_ext`
  import from `uniquode`.
- [ ] 9.2 Move default identity templates into the `auth_ext` package under a
  package template source while keeping logical paths under `identity/`.
- [ ] 9.3 Move any reusable identity static defaults into the `auth_ext` package
  under a package static source while keeping logical paths stable.
- [ ] 9.4 Ensure application templates and static assets can override every
  `auth_ext` identity default by providing the same logical path in the
  application roots.
- [ ] 9.5 Ensure `auth_ext` identity templates rely on application-owned base
  layout and theme context rather than owning product shell or theme state.
- [ ] 9.6 Move identity-specific startup wiring behind installed-module
  composition so a public-only application can omit `auth_ext`.
- [ ] 9.7 Update package metadata so `auth_ext` package templates and static
  assets are included when the project/package is built.
- [ ] 9.8 Add tests proving existing login, signup, logout, account,
  password-reset, and verification pages continue to work through `auth_ext`
  route ownership when `auth_ext` is installed.

## 10. Validation, Tests, And Documentation

- [ ] 10.1 Extend validation to inspect shared composition configuration,
  installed modules, optional module surfaces, `module_routes` exports, model
  metadata, route conflicts, package template sources, package static sources,
  template references, static references, static export inputs, and context
  provider import names.
- [ ] 10.2 Add tests for explicit module inclusion, unlisted module exclusion,
  missing/malformed module errors, deterministic ordering, and optional
  `auth_ext` omission.
- [ ] 10.3 Add tests for context provider resolution, async context merging,
  reserved-key collision failures, provider collision failures, and safe
  identity `user` context.
- [ ] 10.4 Add tests proving future CLI-style consumers can load composition
  configuration and resource sources without importing runtime application
  startup.
- [ ] 10.5 Update README and validation documentation to describe the
  `app.toml` file, `APP_CONFIG`, `installed_modules`, module route prefixes,
  `web_ext`, logical
  template/static paths, application overrides, context providers, static
  export boundary, and development template reload settings.
- [ ] 10.6 Refresh ADR/spec wording that still says identity templates are
  application-owned or that model metadata is loaded from a hard-coded list.
- [ ] 10.7 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate add-application-module-composition --strict`.
