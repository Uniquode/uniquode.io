## 1. `web_core` Core Layer

- [x] 1.1 Create a top-level `web_core` package for shared composition
  configuration, module loading, route/resource/context contracts, and static
  export services.
- [x] 1.2 Move or mirror `HtmlView` and `HtmlRouteDefinition` into the core
  layer without introducing imports from product routes, application settings,
  `auth_ext`, or application FastAPI startup.
- [x] 1.3 Add `ModuleRoutes` and module surface contracts for optional page
  routes, partial routes, API routers, model metadata, package templates,
  package static assets, and context provider registrations.
- [x] 1.4 Add module loading helpers that import explicit module
  names, preserve configured order, and fail clearly on missing modules.
- [x] 1.5 Add import-boundary tests proving `web_core` does not import the
  `uniquode` application package, `auth_ext`, product settings, route modules,
  or deployment secrets.
- [x] 1.6 Allow `web_core` to depend on FastAPI and Starlette engine APIs while
  keeping it independent from a concrete application instance.
- [x] 1.7 Keep application-facing adapters thin so the current `uniquode` app can
  consume `web_core` without an external package extraction in this change.

## 2. Shared Composition Configuration

- [x] 2.1 Add an `app.toml` composition configuration schema and loader with
  `modules` defaults that preserve the current public and
  identity-enabled application surface.
- [x] 2.2 Add composition options for per-module route prefixes, application
  template/static override roots, template reload/cache behaviour, and static
  export defaults.
- [x] 2.3 Add `APP_CONFIG` support so runtime startup, Alembic, validation,
  static export, and future CLIs can use an explicit non-default config path.
- [x] 2.4 Keep the composition loader CLI-safe by avoiding application FastAPI
  startup, Jinja environment construction, route module, `auth_ext`, and
  runtime-secret imports.
- [x] 2.5 Adapt runtime settings to consume the shared composition
  configuration rather than owning a separate module source of truth.
- [x] 2.6 Adapt Alembic and migration metadata loading to consume the shared
  composition loader rather than duplicating module defaults.
- [x] 2.7 Preserve the default `auth.toml` configuration path while allowing
  `app.toml` to reserve compatible auth directives for a separate future
  configuration-unification change.
- [x] 2.8 Add tests for default `app.toml` loading, `APP_CONFIG` override,
  configured ordering, malformed configuration, missing configured modules, and
  CLI-safe imports.
- [x] 2.9 Document the `app.toml` location, `APP_CONFIG` override mechanism,
  schema, future auth-directive compatibility, and distinction from deployment
  secrets or product policy settings.

## 3. Module Surface Discovery

- [x] 3.1 Add surface discovery helpers for conventional model, route,
  template, static, and context-provider surfaces.
- [x] 3.2 Ensure missing optional surfaces are treated as empty contributions.
- [x] 3.3 Ensure malformed present surfaces fail clearly before partial
  application registration.
- [x] 3.4 Ensure template and static package sources are discoverable from
  configured modules without importing route modules.

## 4. Model Metadata Composition

- [x] 4.1 Adapt migration metadata loading to derive model metadata from
  configured modules with conventional `<module>.models` surfaces.
- [x] 4.2 Skip configured modules without model surfaces while preserving clear
  errors for malformed model metadata.
- [x] 4.3 Preserve existing migration metadata ordering and current identity
  table definitions with the default module list.
- [x] 4.4 Add tests proving a public-only module list can omit
  `auth_ext` model metadata.
- [x] 4.5 Add tests proving Alembic can load composed metadata without importing
  runtime application startup.

## 5. Route Composition

- [x] 5.1 Add route module loading helpers that read `module_routes` from
  configured module route surfaces and fail clearly on malformed exports.
- [x] 5.2 Apply configured module route prefixes to relative paths while
  preserving absolute `/`-prefixed route paths.
- [x] 5.3 Convert existing public route registration to publish `module_routes`
  while preserving current paths, route names, and behaviour.
- [x] 5.4 Convert current identity route registration to the module route shape
  before moving ownership to `auth_ext`.
- [x] 5.5 Update the application route registration layer to register page,
  partial, and API routes from configured modules in configured order.
- [x] 5.6 Keep CSRF validation, page/partial surface checks, and API router
  inclusion behaviour equivalent to the current implementation.
- [x] 5.7 Add tests for relative route prefixing, absolute route paths, route
  name conflicts, and method/path conflicts.

## 6. Template Source Composition

- [x] 6.1 Replace the renderer's single filesystem loader with a module-ordered
  logical template loader that searches configured module package templates by
  precedence.
- [x] 6.2 Resolve module template package declarations into Jinja package
  template sources without exposing Jinja loader objects as the public module
  contract.
- [x] 6.3 Preserve stable logical template paths so application overrides use
  the same path as package defaults.
- [x] 6.4 Apply configurable Jinja `auto_reload` and `cache_size` settings and
  cover both reload-friendly and cached configurations in tests.
- [x] 6.5 Add tests for module-order template override precedence,
  module-to-module package template precedence, and missing-template behaviour.

## 7. Static Asset Serving And Export

- [x] 7.1 Replace single-root static serving with a module-ordered logical
  static asset resolver that searches configured module package static sources
  by precedence.
- [x] 7.2 Preserve stable logical static paths so application overrides use the
  same path as package defaults.
- [x] 7.3 Add a collectstatic-style static export service that writes the
  composed logical static namespace into a configured output directory from
  `web_core`.
- [x] 7.4 Ensure static export uses the same precedence rules as runtime static
  serving and writes only the winning asset for each logical path.
- [x] 7.5 Ensure static export can run from the shared composition loader without
  importing application FastAPI startup, route modules, the Jinja environment, or
  identity-specific runtime state.
- [x] 7.6 Add tests for static serving precedence, static export precedence,
  duplicate module defaults, application overrides, and missing assets.

## 8. Template Context Providers

- [x] 8.1 Add a template context provider registry that imports configured
  `<module>.context` surfaces and validates registered context dictionaries or
  request callables once at startup.
- [x] 8.2 Merge provider context dictionaries in configured order before
  view-local context is rendered.
- [x] 8.3 Protect reserved renderer context keys such as `request`,
  `route_name`, and CSRF fields from provider or view overrides.
- [x] 8.4 Fail on provider key collisions by default unless an explicit
  override policy is configured.
- [x] 8.5 Move reusable theme context into a configured context provider rather
  than identity route helpers.
- [x] 8.6 Add an `auth_ext` identity context provider that exposes `user` as a
  safe template view object or `None`, plus non-sensitive identity state.

## 9. Auth Extension Ownership And Optional Inclusion

- [x] 9.1 Move reusable identity views and route definitions from
  `uniquode.routes.identity` into `auth_ext` without adding any `auth_ext`
  import from `uniquode`.
- [x] 9.2 Move default identity templates into the `auth_ext` package under a
  package template source while keeping logical paths under `identity/`.
- [x] 9.3 Move any reusable identity static defaults into the `auth_ext` package
  under a package static source while keeping logical paths stable.
- [x] 9.4 Ensure application templates and static assets can override every
  `auth_ext` identity default by providing the same logical path in the
  application roots.
- [x] 9.5 Ensure `auth_ext` identity templates rely on the composed base layout
  and theme context rather than owning product shell or theme state.
- [x] 9.6 Move identity-specific startup wiring behind module
  composition so a public-only application can omit `auth_ext`.
- [x] 9.7 Update package metadata so `auth_ext` package templates and static
  assets are included when the project/package is built.
- [x] 9.8 Add tests proving existing login, signup, logout, account,
  password-reset, and verification pages continue to work through `auth_ext`
  route ownership when `auth_ext` is installed.

## 10. Validation, Tests, And Documentation

- [x] 10.1 Extend validation to inspect shared composition configuration,
  configured modules, optional module surfaces, `module_routes` exports, model
  metadata, route conflicts, package template sources, package static sources,
  template references, static references, static export inputs, and context
  provider registrations.
- [x] 10.2 Add tests for explicit module inclusion, unlisted module exclusion,
  missing/malformed module errors, deterministic ordering, and optional
  `auth_ext` omission.
- [x] 10.3 Add tests for context provider resolution, async context merging,
  reserved-key collision failures, provider collision failures, and safe
  identity `user` context.
- [x] 10.4 Add tests proving future CLI-style consumers can load composition
  configuration and resource sources without importing runtime application
  startup.
- [x] 10.5 Update README and validation documentation to describe the
  `app.toml` file, `APP_CONFIG`, `modules`, module route prefixes,
  `web_core`, logical
  template/static paths, application overrides, context providers, static
  export boundary, and development template reload settings.
- [x] 10.6 Refresh ADR/spec wording that still says identity templates are
  application-owned or that model metadata is loaded from a hard-coded list.
- [x] 10.7 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate add-application-module-composition --strict`.

## 11. `web_core` Runtime Boundary Refinement

- [x] 11.1 Move the reusable HTML dispatcher, template renderer, CSRF
  protection, form security helpers, route prefix contracts, and generic error
  handling foundation out of `uniquode.web` and into `web_core`.
- [x] 11.2 Move reusable base layout, error templates, theme component
  templates, and baseline stylesheet assets into `web_core` package template and
  static sources.
- [x] 11.3 Move reusable theme state helpers, theme context, and theme partial
  route handling into `web_core`, leaving applications free to omit or override
  them through composition.
- [x] 11.4 Move public-page templates into the owning `public` module so the
  application package no longer owns feature templates by default.
- [x] 11.5 Update the default composition to include `web_core` as the reusable
  lowest-precedence web foundation and keep later modules able to override its
  logical template and static paths.
- [x] 11.6 Update runtime startup, validation, reusable modules, and tests so
  they consume `web_core` directly rather than importing `uniquode.web`.
- [x] 11.7 Remove the `uniquode.web` package once no application-independent
  web runtime logic remains there.

## 12. Core Package Naming

- [x] 12.1 Rename the reusable web infrastructure package and configured module
  to `web_core` so the name reflects a core web interface rather than an
  extension module.

## 13. Project Tooling Boundary

- [x] 13.1 Create a top-level `tools` package for validation command
  orchestration, runtime command orchestration, project-root helpers, and shared
  validation result/check helpers.
- [x] 13.2 Move reusable web-structure validation into `web_core.validation`
  without imports from the `uniquode` application package.
- [x] 13.3 Expose module validation targets through conventional
  `<module>.validation` surfaces and discover them by iterating configured
  modules.
- [x] 13.4 Update the `validate` and `runserver` console scripts, tests,
  documentation, and package metadata to use `tools` entry points.
- [x] 13.5 Add tests for dynamic validation discovery, malformed validation
  surfaces, unlisted modules contributing no targets, and clear unknown-target
  errors.
- [x] 13.6 Run focused validation plus the standard Ruff, ty, pytest, and
  OpenSpec checks.

## 14. `data_core` Data Boundary

- [x] 14.1 Create a top-level `data_core` package for the shared SQLAlchemy
  declarative base, model metadata discovery helpers, migration command, and
  Alembic environment support.
- [x] 14.2 Move conventional `<module>.models` metadata discovery out of
  `web_core` and into `data_core`.
- [x] 14.3 Update `auth_ext.models` to use the shared `data_core` declarative
  base while continuing to expose package-level `metadata`.
- [x] 14.4 Move existing auth/identity migration revision history into
  `auth_ext` and discover module migration version locations from configured
  modules.
- [x] 14.5 Remove the empty `uniquode.models` placeholder and application-owned
  migration files so the application contributes no model metadata or migration
  history until it owns real tables.
- [x] 14.6 Update migration metadata loading, tests, documentation, package
  metadata, and OpenSpec wording for the `data_core` boundary.
- [x] 14.7 Run focused validation plus the standard Ruff, ty, pytest, and
  OpenSpec checks.

## 15. Application Package Boundary Cleanup

- [x] 15.1 Remove empty application-owned package directories that no longer
  contribute runtime surfaces.
- [x] 15.2 Move generic configured-module route registration helpers out of
  `uniquode.routes` and into `web_core`.
- [x] 15.3 Move generic database URL parsing/resolution helpers out of
  `uniquode` and into `data_core`.
- [x] 15.4 Move generic async SQLAlchemy engine/session helpers out of
  `uniquode` and into `data_core`, leaving application startup to adapt
  settings into those helpers.
- [x] 15.5 Critically review `uniquode.validation` and keep only
  application-specific validation targets there, moving reusable data checks
  only if they no longer need application policy.
- [x] 15.6 Update imports, tests, documentation, and packaging expectations for
  the cleaned application boundary.
- [x] 15.7 Run focused validation plus the standard Ruff, ty, pytest, and
  OpenSpec checks.

## 16. Settings Loader Boundary Cleanup

- [x] 16.1 Move reusable environment-setting declarations and typed env value
  parsing helpers out of `uniquode.settings` and into `web_core`.
- [x] 16.2 Move the generic envex/app.toml settings loading algorithm into
  `web_core`, parameterised by a settings factory and optional application
  value loaders.
- [x] 16.3 Reduce `uniquode.settings.load_settings` to an application adapter
  that supplies the `Settings` factory, app env setting declarations, identity
  options loader, and `ConfigurationError` translation.
- [x] 16.4 Keep application-specific `Settings` fields, deployment policy,
  CSRF policy, identity policy, and defaults in `uniquode.settings`.
- [x] 16.5 Add focused tests for the reusable `web_core` settings loader and
  preserve existing application settings behaviour.
- [x] 16.6 Update documentation and OpenSpec wording for the split.
- [x] 16.7 Run focused validation plus the standard Ruff, ty, pytest, and
  OpenSpec checks.

## 17. Review Fixes

- [x] 17.1 Ensure newly introduced package files are included in the tracked
  diff used for review.
- [x] 17.2 Honour explicit filesystem template roots at runtime even when
  configured modules also provide package templates.
- [x] 17.3 Skip identity-specific non-local policy validation when `auth_ext`
  is not configured.
- [x] 17.4 Keep persistence validation passing for no-model compositions that
  intentionally have no module migration revisions.
- [x] 17.5 Pass default module composition into Alembic metadata loading when
  no `app.toml` is available.
- [x] 17.6 Replace unused request deletion in the public home context builder
  with an intentionally unused `_request` parameter.
- [x] 17.7 Replace PEP 695 function type-parameter syntax in the reusable
  settings loader with a `TypeVar` compatible with current tooling targets.
- [x] 17.8 Replace plain `RuntimeError` migration metadata wrapping with a
  dedicated `MigrationConfigError` that preserves the original exception cause.

## 18. Review Follow-up Boundary Fixes

- [x] 18.1 Split the migration command so `data_core` owns the generic Click
  command factory and Alembic config builder while a host adapter injects this
  application's settings loader and defaults.
- [x] 18.2 Remove host application imports from the `data_core` migration command
  and Alembic environment, passing default modules and database URL through
  Alembic configuration instead.
- [x] 18.3 Treat `MigrationConfigError` as an expected configuration failure in
  the migration CLI while leaving unexpected exceptions to surface normally.
- [x] 18.4 Stop runtime static serving and web validation from falling back to
  `web_core` package static assets when `web_core` is omitted and no explicit
  filesystem static root is configured.
- [x] 18.5 Add focused regression coverage for the injected migration adapter,
  `data_core` import boundary, clean metadata configuration errors, and omitted
  `web_core` static assets.

## 19. Review Maintainability Fixes

- [x] 19.1 Add top-level package responsibility docstrings for `web_core`,
  `data_core`, and `tools`, including the imports each boundary must avoid.
- [x] 19.2 Centralise configured-module convention strings for route, context,
  model, migration, template, static, and validation surfaces.
- [x] 19.3 Standardise reusable composition/data/validation/context diagnostic
  message construction while preserving existing exception types and causes.
- [x] 19.4 Preserve the configured `static` route name with an empty static app
  when no static sources are configured, without serving omitted `web_core`
  assets.
- [x] 19.5 Keep settings root classification robust with resolved root
  normalisation coverage and a typed identity environment loader.
- [x] 19.6 Redact sensitive database URL query parameters in addition to
  authority credentials.
- [x] 19.7 Reject blank direct path settings instead of silently treating them
  as default paths.
- [x] 19.8 Document generic loader invariants, settings protocol shapes, and
  shared exception wrapping expectations for reusable web/data/tooling
  boundaries.
- [x] 19.9 Reject invalid non-string HTTP methods during route composition and
  add broader boundary tests for `data_core` and `tools`.
