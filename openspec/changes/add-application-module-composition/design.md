## Context

The current application is composed in several hard-coded places:

- model metadata is loaded from a fixed tuple in `uniquode.migration_metadata`;
- public and identity routes are registered directly by `uniquode.routes`;
- templates are loaded from a single filesystem root;
- static assets are served from a single filesystem root;
- template context is built by the renderer plus route-local helpers.

That was acceptable while `uniquode` owned the full browser surface. It no
longer matches the package boundary we want. Reusable packages should be able to
own their models, routes, default templates, static assets, and template
context. The host application should explicitly decide which modules are part
of the app and how their resources are placed and overridden.

The shape is intentionally similar to Django's `INSTALLED_APPS`, but the route
model should stay more explicit than Django's single top-level URL module. In
particular, the host application should be able to choose a default route
prefix for a module, while a module can still declare an absolute route path
when it intentionally owns a root-level path such as `/login`.

The composition source also needs to be useful outside the web runtime. Alembic,
validation, a collectstatic-style exporter, and future project CLIs should be
able to load the installed module list and resource configuration without
booting the FastAPI application or importing runtime-only settings.

## Goals / Non-Goals

**Goals:**

- Introduce `app.toml` as the shared, file-backed composition configuration
  whose ordered `installed_modules` list is the source of truth for enabled
  application modules.
- Support `APP_CONFIG` as the environment override for the composition
  configuration path.
- Keep the composition configuration loader independent from FastAPI
  application construction, Jinja environment construction, application
  startup, and identity-specific runtime state so it can be reused by Alembic
  and future CLIs.
- Introduce a top-level `web_ext` package as an application-independent,
  opinionated web composition layer over FastAPI.
- Let installed modules optionally contribute model metadata, routes,
  templates, static assets, and template-context providers.
- Make `auth_ext` optional from the application composition perspective: a
  public-only application can omit it and avoid loading identity web/data
  surfaces.
- Keep composition explicit. Installed packages must not silently mount
  themselves.
- Preserve deterministic ordering and override precedence for templates,
  static assets, and context providers.
- Let the host application configure default route prefixes for module routes.
- Provide a collectstatic-style static export boundary that can consolidate
  application and module static assets from the composition configuration.
- Fail clearly on route conflicts, malformed module surfaces, missing required
  modules, and invalid context providers.
- Keep application-level theme, layout chrome, branding, navigation, redirects,
  delivery, and policy in the host application.
- Create a clean extraction seam for a future reusable composition package
  without extracting it in this change.

**Non-Goals:**

- Do not scan installed distributions automatically.
- Do not introduce a frontend build pipeline or new external runtime
  dependency.
- Do not move application theme ownership into `auth_ext`.
- Do not make templates or static assets the source of authorisation
  decisions.
- Do not introduce Django-style model/table-name prefixing in this change.
- Do not extract an external package in this change.
- Do not make the composition configuration a general secrets or deployment
  settings file.
- Do not merge the existing auth configuration into `app.toml` in this change;
  `app.toml` may reserve space for those directives, but `auth.toml` remains
  the default auth configuration file for now.
- Do not require a concrete static-collection CLI command before the
  composition/export boundary exists.

## Decisions

### Use File-Backed Composition As The Composition Root

Add a small project configuration file, expressed as TOML so the implementation
can use Python's standard `tomllib`, that owns the composition inputs. The
default filename is `app.toml`. The parser should normalise this shape into
typed composition options:

```toml
[composition]
installed_modules = [
  "uniquode",
  "public",
  "auth_ext",
]

[composition.route_prefixes]
auth_ext = "/"
```

The loader should read the default `app.toml` from the project/application root
unless `APP_CONFIG` points at a different path. `APP_CONFIG` is the process-wide
override used by runtime startup, Alembic, validation, static export tooling,
and future CLIs. A future concrete CLI may also expose an explicit config-path
flag, but the reusable loader should not depend on a CLI existing.

The configuration name is intentionally generic. It is not tied to `uniquode`,
because `uniquode` is the application consuming the framework. `app.toml` may
later contain directives currently represented in `auth.toml` if unifying
configuration becomes useful, but this change should leave the default
`auth.toml` behaviour alone and handle auth configuration migration separately.

The list defines which modules are enabled and gives deterministic composition
order. Missing configured modules fail at startup or validation. Installed
packages not listed here contribute nothing.

The intended order is base-to-specific. Core modules appear first; feature or
extension modules appear later. The application itself remains the final owner
for product policy and resource overrides.

Runtime settings should adapt this file-backed composition into application
startup options rather than owning the composition source of truth. Alembic,
validation, static-asset collection, and future CLIs should call the same
composition loader and should not construct the application FastAPI instance,
construct the Jinja environment, or import `auth_ext` just to learn which
modules are installed.

Alternative considered: keep separate settings such as `enabled_route_modules`
and `enabled_model_packages`. That is simpler for the current implementation
but causes drift as modules gain more surfaces. A single composition root better
matches the mental model the application needs.

Alternative considered: keep the composition list only on runtime `Settings`.
That keeps the current settings model simple, but it couples Alembic and future
CLIs to web-runtime state or duplicated defaults. A small shared file-backed
configuration gives every process the same module graph while preserving a
thin runtime settings adapter.

### Add `web_ext` As The Application-Independent Core Layer

The amount of shared behaviour now justifies an internal core package rather
than scattering composition code through the `uniquode` application package.
Create it as a top-level `web_ext` module. `web_ext` is not intended to be
engine-agnostic; it is an opinionated composition framework over FastAPI that
uses FastAPI, Starlette, and Jinja2 where those tools already fit.

`web_ext` should own:

- file-backed composition configuration parsing and normalisation;
- installed-module import and optional surface discovery;
- web route/resource/context contracts such as `HtmlView`,
  `HtmlRouteDefinition`, and `ModuleRoutes`;
- template and static source resolution;
- context-provider registry contracts;
- static export services.

`web_ext` should not import product routes, product settings, `uniquode.app`,
`auth_ext`, this application's FastAPI startup, or deployment secrets. The
current application, Alembic, validation, static export tooling, and future
CLIs should all be consumers of `web_ext`. `auth_ext` may also depend on
`web_ext` contracts to publish identity module surfaces, but `web_ext` must not
depend on `auth_ext`. Extracting `web_ext` into a separately published package
remains a future step; this change should create the boundary without adding
packaging complexity before it is needed.

### Discover Optional Module Surfaces By Convention

Each installed module may expose conventional surfaces:

```text
<module>.models      -> SQLAlchemy metadata, if present
<module>.routes      -> module_routes, if present and web routes are needed
<module>/templates   -> package template source, if present
<module>/static      -> package static source, if present
<provider import>    -> async context providers declared by module routes
```

Missing optional surfaces are no-ops. Malformed present surfaces fail clearly.
Template and static package sources should be discoverable from the installed
module list without importing route modules. That keeps static collection and
template validation usable by CLIs that do not need web route registration.

The model convention builds on the existing `load_model_metadata()` shape:
model packages expose top-level SQLAlchemy `metadata`. The initial
implementation can adapt `installed_modules` into model package names such as
`<module>.models` and load the metadata that exists.

Model/table naming collisions are a known future consideration. Django avoids
many collisions with app-label prefixes; this project already uses explicit
table names and can continue doing so. Prefixing or app-labelled table naming is
YAGNI for this change and should be revisited only when there is a concrete
collision or multi-app packaging requirement.

### Keep Module Routes Explicit But Prefixable

Route modules continue to publish a `module_routes` object. The host
application controls whether the module is installed and can configure the
module's default route prefix.

Module route path handling should follow a simple rule:

- relative paths are mounted below the module's configured route prefix;
- absolute `/`-prefixed paths are used as-is.

This keeps module defaults portable while allowing intentional root-level
routes. For example, an identity module might use absolute `/login` and
`/account` paths in this application, while another host could configure
relative identity paths below `/identity` if the module declares them that way.

Route registration remains conflict-intolerant. Conflicting route names or
method/path pairs should fail validation/startup rather than relying on order.

Alternative considered: a Django-style single `urls.py` delegation tree. That
is flexible, but it centralises too much route wiring in the host and does not
fit the existing `HtmlRouteDefinition` dispatcher well.

### Preserve Separate Route Surfaces

`ModuleRoutes` should keep page routes, partial routes, and API routers
separate. Page and partial routes bind route metadata to view objects that
render full templates or fragments. API routers remain FastAPI routers and stay
machine-oriented.

This preserves existing page/partial/API policies, including CSRF and
validation differences.

### Use Logical Template And Static Namespaces

Templates and static assets should both use logical resource paths. The
application owns override roots:

```text
src/templates/
src/static/
```

Installed modules may ship package defaults:

```text
src/auth_ext/templates/identity/pages/login.html
src/auth_ext/static/identity/login.css
```

Lookup precedence should be:

1. application override root;
2. installed module package sources in reverse `installed_modules` order.

Reverse module order gives later, more specific modules higher default
precedence while still allowing the application root to override everything.
Modules should avoid intentionally sharing logical paths unless they are
designed as replacements. Validation should report duplicate module defaults so
the precedence is visible.

For static assets, the initial implementation should keep the serving model
simple: resolve and return the first matching logical asset. Fingerprinting,
manifest generation, bundling, and CDN integration are out of scope.

### Add A Static Collection Boundary

Static serving from multiple package sources is useful in development, but
deployments and future CLIs need a way to materialise the same logical static
namespace into a directory. The composition core should expose a
collectstatic-style operation that:

- loads composition configuration through the shared file-backed loader;
- enumerates the application static root and installed module package static
  sources in the same precedence order used by runtime serving;
- copies only the winning asset for each logical path into a configured output
  directory;
- reports duplicate module defaults and application overrides consistently with
  validation.

This operation belongs in `web_ext`, because it is a general web composition
concern rather than an identity concern. It should be a reusable service
boundary first. A concrete CLI can be added later and can delegate to it
without needing to import application FastAPI startup code, route modules, the
Jinja environment, or identity-specific runtime state.

### Keep Application Layout And Theme Above Module Templates

Module templates can provide page content, forms, fragments, and module-local
components. The application owns the outer layout and theme. Identity templates
should extend a stable logical base template such as `layouts/page.html`; the
application provides that template.

Theme context should be contributed by an application-owned context provider.
`auth_ext` should not inject or own product theme state.

### Resolve Context Providers From Configurable Import Strings

Modules publish context provider names as strings, not already-imported
callables. The application can append, remove, replace, or reorder provider
names before startup resolution.

At startup, the application resolves each provider string once, validates that
it is an async request callable, and stores callable providers for request-time
execution.

At request time, context is built in layers:

1. internal reserved context such as `request`, `route_name`, and CSRF fields;
2. module provider context dictionaries in configured order;
3. application provider context dictionaries;
4. view-local context.

Reserved key collisions should fail loudly. Non-reserved provider collisions
should be forbidden by default. If replacement semantics are needed later, they
should be explicit in configuration rather than accidental.

For identity, `auth_ext` should expose a provider that contributes a safe
template user object:

```python
{
    "user": TemplateUser(...) | None,
    "identity": {"authenticated": bool, ...},
}
```

The user object must not expose password hashes, tokens, raw ORM
relationships, or reset/verification internals.

### Keep `auth_ext` Optional At Composition Time

`auth_ext` should still be a project dependency while the current product uses
identity, but composition must not assume it is installed into every app
instance. If `auth_ext` is omitted from `installed_modules`, the application
must not load auth models, auth routes, auth templates, auth static assets, auth
context providers, or auth-specific startup wiring.

That does not mean every existing application setting becomes optional in the
same edit. It does mean startup should move identity-specific setup behind the
composition boundary as this change is implemented.

## Risks / Trade-offs

- [Risk] This broadens the change beyond web routes/templates. → Mitigation:
  keep the implementation incremental and preserve current behaviour through
  default `installed_modules`.
- [Risk] Model metadata, Alembic configuration, and future CLIs may drift from
  runtime settings. → Mitigation: make `app.toml` and the shared `web_ext`
  composition loader the source for runtime settings, migration metadata
  loading, validation, and static export.
- [Risk] Routes can conflict once multiple modules contribute surfaces. →
  Mitigation: fail validation/startup on route-name or method/path conflicts.
- [Risk] Template or static duplicates can be surprising. → Mitigation:
  application root always wins; module default precedence is deterministic;
  validation reports duplicate module defaults.
- [Risk] Static collection can accidentally couple to web startup. →
  Mitigation: make static source discovery work from installed modules and
  package resources without importing route modules or application startup.
- [Risk] Context providers can create surprising key collisions. → Mitigation:
  reserve internal keys and forbid provider collisions by default.
- [Risk] Moving identity routes into `auth_ext` can introduce a reverse
  dependency on `uniquode`. → Mitigation: keep generic route/view contracts in
  `web_ext` and continue import-boundary tests for `auth_ext`.

## Migration Plan

1. Add `web_ext`, composition contracts, the shared `app.toml` loader, and
   module-surface loaders while keeping current behaviour intact.
2. Add `installed_modules` defaults for the current application in `app.toml`
   and adapt runtime settings to consume it.
3. Adapt model metadata loading and Alembic wiring to derive from installed
   modules through the same loader.
4. Convert existing public and identity route registration to `module_routes`.
5. Add template and static source composition with application-first
   precedence.
6. Add a collectstatic-style static export service over the composed static
   namespace.
7. Add context-provider registration and move theme context out of identity
   route helpers into an application provider.
8. Move identity routes and default identity templates into `auth_ext`, keeping
   logical paths stable so application overrides continue to work.
9. Move identity startup wiring behind installed-module composition.
10. Update validation to inspect installed module surfaces and static export
    inputs.
11. Refresh ADR/spec wording that currently assumes identity templates are
    application-owned.

Rollback is straightforward while route paths and template names remain stable:
the application can keep `auth_ext` installed and re-enable host-owned identity
route registration until the module-owned path is ready.
