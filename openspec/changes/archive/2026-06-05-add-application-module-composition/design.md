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
able to load the configured module list and resource configuration without
booting the FastAPI application or importing runtime-only settings.

## Goals / Non-Goals

**Goals:**

- Introduce `app.toml` as the shared, file-backed composition configuration
  whose ordered `modules` list is the source of truth for enabled application
  modules.
- Support `APP_CONFIG` as the environment override for the composition
  configuration path.
- Keep the composition configuration loader independent from FastAPI
  application construction, Jinja environment construction, application
  startup, and identity-specific runtime state so it can be reused by Alembic
  and future CLIs.
- Introduce a top-level `web_core` package as an application-independent,
  opinionated web composition layer over FastAPI.
- Introduce a top-level `data_core` package for reusable SQLAlchemy data
  modelling contracts and configured model metadata discovery.
- Let configured modules optionally contribute model metadata, routes,
  templates, static assets, template-context providers, and validation targets.
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
- Keep application-specific branding, navigation, redirects, delivery, and
  policy in the host application, while allowing `web_core` to provide reusable
  default layout, theme, error, form, and static assets that host applications
  can omit or override.
- Move project command orchestration into a top-level `tools` package, with
  validation targets discovered from configured module validation surfaces
  rather than from a hard-coded application registry.
- Create a clean extraction seam for a future reusable composition package
  without extracting it in this change.

**Non-Goals:**

- Do not scan installed distributions automatically.
- Do not introduce a frontend build pipeline or new external runtime
  dependency.
- Do not move reusable or application theme ownership into `auth_ext`.
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
modules = [
  "uniquode",
  "public",
  "auth_ext",
]

[routes]
auth_ext = "/"

[templates]
auto_reload = true
cache_size = 0

[static]
url_path = "/static/"
export_root = "static"
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

The mechanics of adapting envex values plus `app.toml` into a concrete settings
object are also reusable. `web_core` should provide the generic settings loader
that handles typed environment values, app configuration discovery, and settings
factory invocation. The host application still owns the concrete `Settings`
class, application defaults, deployment policy, CSRF policy, and identity
options adapter.

Alternative considered: keep separate settings such as `enabled_route_modules`
and `enabled_model_packages`. That is simpler for the current implementation
but causes drift as modules gain more surfaces. A single composition root better
matches the mental model the application needs.

Alternative considered: keep the composition list only on runtime `Settings`.
That keeps the current settings model simple, but it couples Alembic and future
CLIs to web-runtime state or duplicated defaults. A small shared file-backed
configuration gives every process the same module graph while preserving a
thin runtime settings adapter.

### Add `web_core` As The Application-Independent Core Layer

The amount of shared behaviour now justifies an internal core package rather
than scattering composition code through the `uniquode` application package.
Create it as a top-level `web_core` module. `web_core` is not intended to be
engine-agnostic; it is an opinionated composition framework over FastAPI that
uses FastAPI, Starlette, and Jinja2 where those tools already fit.

`web_core` should own:

- file-backed composition configuration parsing and normalisation;
- reusable envex/app.toml settings-loading mechanics;
- module import and optional surface discovery;
- web route/resource/context contracts such as `HtmlView`,
  `HtmlRouteDefinition`, and `ModuleRoutes`;
- the reusable HTML dispatcher, template renderer, CSRF/form security helpers,
  route prefix contracts, and error handler foundation;
- template and static source resolution;
- context-provider registry contracts;
- reusable default layout, error, theme, component, and stylesheet resources;
- static export services.

`web_core` should not import product routes, product settings, `uniquode.app`,
`auth_ext`, this application's FastAPI startup, or deployment secrets. The
current application, Alembic, validation, static export tooling, and future
CLIs should all be consumers of `web_core`. `auth_ext` may also depend on
`web_core` contracts to publish identity module surfaces, but `web_core` must not
depend on `auth_ext`. Extracting `web_core` into a separately published package
remains a future step; this change should create the boundary without adding
packaging complexity before it is needed.

### Add `data_core` For Reusable Data Infrastructure

SQLAlchemy model metadata discovery and a shared declarative base are data
infrastructure, not web infrastructure and not application product code. Create
a top-level `data_core` package to own these reusable pieces. `data_core` should
provide:

- a shared SQLAlchemy `DeclarativeBase` and its `metadata`;
- conventional `<module>.models` package discovery;
- validation of exported SQLAlchemy `metadata` objects; and
- deterministic conversion from configured module names to model packages.

`web_core` may need to report configured web surfaces, but it should not import
SQLAlchemy or own model metadata discovery. Application migration metadata
loading should call `data_core` directly. Reusable data modules such as
`auth_ext` should import their declarative base from `data_core` and continue
to expose package-level `metadata` for host applications that include the
module.

Migrations are repository-owned schema history, not a live reflection of the
database. The database records which revisions have been applied; the revision
files describe how the repository expects the configured database schema to
evolve. The migration graph is database-wide at runtime, but revision files do
not need to live in one global application directory. `data_core` should own the
Alembic runner, environment, script template, and discovery of configured
module migration locations. Modules that own tables should own the revision
files for those tables under a conventional migration directory. Cross-module
schema dependencies should be represented in revision metadata rather than by
moving all revisions back into the host application package.

The current `uniquode.models` package does not define application-owned tables.
Keeping it solely to publish an empty `Base.metadata` creates a false
application ownership signal. Remove it until the host application has real
application data models. The configured `uniquode` module can still contribute
routes and validation targets without contributing a model surface.

### Discover Optional Module Surfaces By Convention

Each configured module may expose conventional surfaces:

```text
<module>.models      -> SQLAlchemy metadata, if present
<module>.routes      -> module_routes, if present and web routes are needed
<module>/templates   -> package template source, if present
<module>/static      -> package static source, if present
<module>.context     -> context provider registrations, if present
<module>.validation  -> named validation targets, if present
```

Missing optional surfaces are no-ops. Malformed present surfaces fail clearly.
Template and static package sources should be discoverable from the installed
module list without importing route modules. That keeps static collection and
template validation usable by CLIs that do not need web route registration.

The model convention builds on the existing `load_model_metadata()` shape:
model packages expose top-level SQLAlchemy `metadata`. The implementation
adapts `modules` into model package names by looking for `<module>.models` and
loading the metadata that exists.

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

Templates and static assets should both use logical resource paths. Configured
modules may ship package sources:

```text
src/web_core/templates/layouts/page.html
src/web_core/static/styles/app.css
src/public/templates/public/pages/home.html
src/auth_ext/templates/identity/pages/login.html
src/auth_ext/static/identity/login.css
```

Lookup precedence should be:

1. configured module package sources in reverse `modules` order.

Reverse module order gives later, more specific modules higher default
precedence. The application can still override another module by placing its
resource-owning module later in `modules`. Modules should avoid intentionally
sharing logical paths unless they are designed as replacements. Validation
should report duplicate module defaults so the precedence is visible.

For static assets, runtime serving should resolve configured module package
sources directly and return the first matching logical asset. It must not
assume assets have already been collected into an export directory. Static
collection is required only for deployment shapes where an external static
server such as Nginx serves the assets. Fingerprinting, manifest generation,
bundling, and CDN integration are out of scope.

### Add A Static Collection Boundary

Static serving from multiple package sources is useful in development, but
deployments and future CLIs need a way to materialise the same logical static
namespace into a directory. The composition core should expose a
collectstatic-style operation that:

- loads composition configuration through the shared file-backed loader;
- enumerates configured module package static sources in the same precedence
  order used by runtime serving;
- copies only the winning asset for each logical path into a configured output
  directory;
- reports duplicate module defaults consistently with validation.

This operation belongs in `web_core`, because it is a general web composition
concern rather than an identity concern. It should be a reusable service
boundary first. A concrete CLI can be added later and can delegate to it
without needing to import application FastAPI startup code, route modules, the
Jinja environment, or identity-specific runtime state.

### Keep Reusable Layout And Theme In `web_core`

Module templates can provide page content, forms, fragments, and module-local
components. `web_core` provides a reusable outer layout, error templates,
theme selector component, theme context provider, and baseline stylesheet as
default module resources. Applications can opt out by omitting `web_core`, or
override those defaults by providing the same logical template and static paths
from a later configured module.

Identity templates should extend a stable logical base template such as
`layouts/page.html`; the composed module namespace decides whether that base
comes from `web_core` or an application override. `auth_ext` should not inject or
own product theme state.

### Resolve Context Providers From Module Registrations

Configured modules may publish a `<module>.context` surface. Importing that
surface lets the module call `add_to_context` to register static context
dictionaries or request-time provider callables. There is no separate context
section in `app.toml`; module inclusion and ordering are the composition
source of truth.

At startup, the application imports configured context surfaces once, validates
registered providers, and stores callable providers for request-time execution.

At request time, context is built in layers:

1. internal reserved context such as `request`, `route_name`, and CSRF fields;
2. registered module provider context dictionaries in configured order;
3. view-local context.

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
instance. If `auth_ext` is omitted from `modules`, the application
must not load auth models, auth routes, auth templates, auth static assets, auth
context providers, or auth-specific startup wiring.

That does not mean every existing application setting becomes optional in the
same edit. It does mean startup should move identity-specific setup behind the
composition boundary as this change is implemented.

### Keep Project Commands In `tools`

Concrete project commands such as `validate` and `runserver` are tooling rather
than application runtime. They should live in a top-level `tools` package so
they are not owned by the `uniquode` host application package. These commands
may still load the current project's settings adapter or target the current
ASGI app, but command orchestration, project-root helpers, target discovery,
shared validation result types, and output handling belong to `tools`.

Validation targets should follow the same explicit module-composition rule as
routes, templates, static assets, models, and context providers. A configured
module may expose a conventional `<module>.validation` surface with a
`validation_targets` mapping from target name to callable. The `validate`
command iterates the configured `modules` list, imports present validation
surfaces, validates the mapping shape, and runs the requested targets in
discovered order. Missing validation surfaces are empty contributions; malformed
surfaces fail clearly before checks are run.

Reusable web validation belongs with the reusable web foundation. `web_core`
should publish the `web` validation target from its validation surface and must
not import the `uniquode` application package to build configured route,
template, static, or context checks. Application-specific environment and
persistence validation can remain under `uniquode.validation` as validation
targets contributed by the configured `uniquode` module when they check this
application's supported environment variable list, default database filename,
or identity-table expectations. Generic route registration belongs in
`web_core`; generic database URL parsing, URL redaction, and async SQLAlchemy
engine/session helpers belong in `data_core`.

This keeps the current `validate` executable behaviour while removing the
application-owned registry. Future modules can add validation without modifying
the command or the host application package; the host still decides whether a
module's validation exists by including that module in `app.toml`.

## Risks / Trade-offs

- [Risk] This broadens the change beyond web routes/templates. → Mitigation:
  keep the implementation incremental and preserve current behaviour through
  default `modules`.
- [Risk] Model metadata, Alembic configuration, and future CLIs may drift from
  runtime settings. → Mitigation: make `app.toml` and the shared `web_core`
  composition loader the source for runtime settings, migration metadata
  loading, validation, and static export.
- [Risk] Routes can conflict once multiple modules contribute surfaces. →
  Mitigation: fail validation/startup on route-name or method/path conflicts.
- [Risk] Template or static duplicates can be surprising. → Mitigation:
  application root always wins; module default precedence is deterministic;
  validation reports duplicate module defaults.
- [Risk] Static collection can accidentally couple to web startup. →
  Mitigation: make static source discovery work from configured modules and
  package resources without importing route modules or application startup.
- [Risk] Context providers can create surprising key collisions. → Mitigation:
  reserve internal keys and forbid provider collisions by default.
- [Risk] Moving identity routes into `auth_ext` can introduce a reverse
  dependency on `uniquode`. → Mitigation: keep generic route/view contracts in
  `web_core` and continue import-boundary tests for `auth_ext`.
- [Risk] Validation target discovery can hide target availability behind module
  configuration. → Mitigation: keep discovery deterministic from `modules`,
  fail clearly on unknown requested targets, and cover dynamic surfaces in
  tests.
- [Risk] Shared ORM metadata can be contributed more than once when several
  modules import the same `data_core` base. → Mitigation: model metadata
  loading should preserve configured module order while de-duplicating identical
  metadata objects by identity before handing them to Alembic.
- [Risk] Module-owned migration revisions can create multiple Alembic heads or
  cross-module ordering requirements. → Mitigation: keep the runtime migration
  graph database-wide, discover version directories only from configured
  modules, and use Alembic revision dependencies when one module's schema
  depends on another module's tables.

## Migration Plan

1. Add `web_core`, composition contracts, the shared `app.toml` loader, and
   module-surface loaders while keeping current behaviour intact.
2. Add `modules` defaults for the current application in `app.toml`
   and adapt runtime settings to consume it.
3. Adapt model metadata loading and Alembic wiring to derive from configured
   modules through the same loader.
4. Convert existing public and identity route registration to `module_routes`.
5. Add template and static source composition with module-order precedence.
6. Add a collectstatic-style static export service over the composed static
   namespace.
7. Add context-provider registration and move reusable theme context out of
   identity route helpers into the `web_core` module provider.
8. Move identity routes and default identity templates into `auth_ext`, keeping
   logical paths stable so application overrides continue to work.
9. Move identity startup wiring behind module composition.
10. Update validation to inspect configured module surfaces and static export
    inputs.
11. Move `validate` and `runserver` command orchestration into `tools` and
    discover validation targets from configured module validation surfaces.
12. Move reusable data modelling, model metadata discovery, migration command
    orchestration, and Alembic environment support into `data_core`; move
    module-specific revision history into the owning modules; and remove empty
    `uniquode` data placeholders.
13. Move remaining generic configured-route registration and database
    URL/session helpers out of the host application package, keeping only
    application-specific health, settings, startup, environment, and validation
    policy there.
14. Move reusable envex/app.toml settings-loading mechanics into `web_core`,
    leaving the concrete application `Settings` class and policy in
    `uniquode.settings`.
15. Refresh ADR/spec wording that currently assumes identity templates are
    application-owned.

Rollback is straightforward while route paths and template names remain stable:
the application can keep `auth_ext` installed and re-enable host-owned identity
route registration until the module-owned path is ready.
