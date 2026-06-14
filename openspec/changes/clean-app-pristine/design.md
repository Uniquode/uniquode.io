## Context

The host application still contains configuration and environment scaffolding that predates Wevra-owned startup, module setup, and config services. Files such as `config_definitions.py` and `environment.py` make the app responsible for concerns that now belong to Wevra or to configured modules.

The target shape is a pristine host app: app-owned routes, views, context, and product settings only. The app may still include a small `validation.py` module when it performs product-specific checks, such as validating its home page template and assets. Generic environment loading, config definition handling, validation, module startup, database setup, auth setup, static/template composition, and route discovery belong inside Wevra or the module that owns the behaviour.

## Goals / Non-Goals

**Goals:**

- Remove app-owned Wevra scaffolding that remains after the site startup refactor.
- Move reusable configuration definition, environment loading, parsing, and validation support into Wevra when still required.
- Require configured modules to own their own config definitions and typed settings loaders.
- Keep the app capable of running without database, auth, or other optional Wevra modules.
- Make absence explicit: omitted modules or config do not trigger fallback database/auth/static behaviour.
- Simplify or encapsulate `envex` usage so host apps do not wrap it directly.

**Non-Goals:**

- Introduce compatibility shims for old app-side startup/configuration paths.
- Add a new configuration system beyond the Wevra config-service boundary.
- Require `wevra.db`, `wevra.auth`, or any specific module for a basic site.
- Preserve app-owned environment loader entry points merely because tests or old tooling use them.
- Implement the `wevra-create` generator; that is covered by `add-wevra-create-generator`.

## Decisions

### Wevra owns generic environment loading

Wevra will provide the environment source and any required dotenv handling for normal site startup and Wevra-owned CLI commands. The host app will not define an `environment.py` wrapper for Wevra concerns.

Alternative considered: keep a thin app wrapper around `envex.Env`. This keeps the wrong boundary and forces every app to copy framework bootstrap code, so it is rejected.

### Modules own config definitions and typed settings

Config definitions will live with the module or Wevra platform component that owns the setting. The host app may define product-specific config, but it will not aggregate config fields for auth, database, static, templates, validation, or other Wevra-owned concerns.

Alternative considered: keep a central app `config_definitions.py` as an integration manifest. This duplicates the configured module list and makes modules reach across ownership boundaries, so it is rejected.

### Config fields own resolution metadata

`ConfigDef` sections declare ordered `ConfigField` values. Each field owns its config name, optional default value, optional environment binding, and optional `transform` callable. This keeps the field's resolution metadata together instead of splitting field names, defaults, environment variables, and transforms across parallel mappings.

The transform receives the resolved parsed value and returns the typed or normalised value consumed by settings and module setup. The transform runs after defaults, config sources, and environment overrides have been resolved, so precedence remains centralised in the config service. If no transform is declared, the resolved value is copied through unchanged.

Transforms are ordinary callables, so modules can use constructors such as `Path`, shared helpers such as boolean normalisers, or `functools.partial` for root-aware path resolution. Invalid transform input fails configuration loading with field context instead of forcing startup code to duplicate parsing and validation.

Alternative considered: keep field names, defaults, and environment bindings as separate mappings on `ConfigGroup`. That creates avoidable drift checks and hides the full declaration of a field, so it is rejected.

### App config declarations are separate from app settings classes

An app that owns product settings will declare those fields through an app-owned `module_config` in `app/config.py`. The app `Settings` type is the typed target object and carries its owning module `ConfigDef` as class-level metadata. The `ConfigDef` remains app-owned in `app.config`; the settings class binds to it so loaders do not need to search for a separate config definition or pass it at every call site.

For the normal case where a settings class is backed by a single-section `ConfigDef`, Wevra infers the section and passes only fields declared by that `ConfigDef` into the settings object. Settings classes backed by multi-section config definitions must name their section explicitly because there is no safe generic inference rule.

For this app, `[app].name` is stable app-owned identity and belongs in `app.config.module_config`. It is not environment-overridable. `deployment_environment` is Wevra-owned runtime configuration and must remain in Wevra runtime/config handling. A combined `APP_SETTINGS_CONFIG_DEF` that contains both fields is therefore the wrong boundary and should be split or removed.

Alternative considered: keep `wevra.core.config.APP_SETTINGS_CONFIG_DEF` and let app settings import it. This forces apps to depend on a Wevra-owned config bundle and mixes product settings with runtime platform settings, so it is rejected.

### Settings shrink to app-owned values

The host app `Settings` type will retain only values the product app actually owns. Module-owned settings will be loaded from the central config service by the owning module or through an explicit public capability/helper.

Alternative considered: retain bridged settings fields for startup convenience. That repeats the old coupling and blocks modules from being replaced by compatible capability providers, so it is rejected.

### Generated apps show extension points without requiring them

The cleaned app is also the reference shape for generated sites. It should expose important extension points even when they are currently no-ops, so developers can discover how app-owned setup is intended to work. The app package therefore includes a documented `setup_site` stub in the app startup module and re-exports it from `__init__.py` for Wevra discovery. The stub is explicitly optional and can be removed when the app has no app-specific capabilities, services, or lifecycle setup.

Alternative considered: omit the hook until the app needs active startup work. This keeps the runtime minimal but hides an important extension point from generated apps, so it is rejected for the reference app shape.

### Wevra owns settings loading mechanics

Settings loading is a Wevra concern. Host apps should not expose `load_settings(environ, project_root, read_dotenv)` because those arguments describe environment source selection, project-root discovery, dotenv policy, and config-source resolution. Those belong to Wevra.

The app should declare the settings it owns through `ConfigDef`, bind that definition to a typed `Settings` object, and receive loaded settings from Wevra through a public loader or site API. CLI arguments, environment variables, config files, and future config sources are resolved by Wevra before typed settings are constructed.

Alternative considered: keep app-local `load_settings()` as a thin wrapper over Wevra config APIs. Even as a wrapper, it makes the app responsible for Wevra config mechanics and creates another copy point for generated apps, so it is rejected.

### Wevra tools own project settings for module validation and migrations

Wevra CLI tools that validate or migrate module-owned concerns will build their own project settings from `app.toml`, Wevra-owned environment loading, and discovered module config definitions. The host app settings loader is not used as an adapter for database URLs, Alembic paths, static roots, template roots, or renderer settings.

Alternative considered: keep `[tool.wevra].settings_loader` and require each host app to expose Wevra-owned fields on its app settings object. This keeps the wrong coupling and makes generated apps carry framework internals, so it is rejected.

### Web owns request context and runtime static handling

Wevra web setup will own the default template context supplied for each request and the runtime static ASGI app selection. The request object is available to templates by default so templates can access request URL, path, scheme, headers, and related request attributes; this is controlled by a Wevra web setting and can be disabled explicitly.

Template context accumulation will use an immutable `TemplateContext` value object rather than passing raw mutable dictionaries between providers. Wevra initialises an empty context per request, providers receive `(request, context)`, and providers return a new context with their additions. The app `context.py` provider should follow that shape so it can inspect existing context without mutating it in place.

Template context keys use first-wins merge semantics. Wevra seeds framework render values first, including the request object when request context is enabled, then merges direct view context and request-wide provider context. Providers and views may read previously accumulated context, but attempted overwrites are ignored and logged at warning level rather than raising. If request context is disabled, Wevra does not seed the request object; a provider or view may still add one explicitly because no special protected-key list is enforced.

Filesystem static serving is enabled only when a static root is configured. When no static root is configured, Wevra serves configured module static assets or the empty static app when no static source exists.

Alternative considered: keep `StaticFiles` construction and request context defaults in each host app. This repeats framework boilerplate and makes generated apps responsible for Wevra-owned web concerns, so it is rejected.

### ASGI entry point is a Wevra shim

Host apps should expose their ASGI application with a tiny entry point that imports their app factory and delegates common configuration-error handling to Wevra. The expected shape is `app = load_asgi_app(create_app)`.

Alternative considered: keep configuration exception handling in every generated app `asgi.py`. This is repeated framework boilerplate, so it is rejected.

### Absence means absence

No default/fallback database, auth, route, static, template, or module behaviour will be synthesised because a host app omitted configuration. A Wevra site must be valid without database/auth when those modules are absent.

Alternative considered: infer default modules or fallback config for convenience. That makes configuration surprising and ties sites to modules they did not request, so it is rejected.

### `envex` becomes an internal detail if retained

If Wevra still needs `envex` for encrypted dotenv support, bool/int parsing, path handling, or environment lookup, that usage will be encapsulated in Wevra-owned code. If those features are not needed, the implementation should reduce or remove the dependency rather than preserving it by inertia.

Alternative considered: keep `envex` as an app-facing integration point. That exposes too much low-level environment handling to generated/basic apps, so it is rejected.

## Risks / Trade-offs

- [Risk] Existing tests may assert app-level environment/config objects that should no longer exist. → Replace them with Wevra/module tests for the owner behaviour and app tests for composition outcomes.
- [Risk] CLI tools may currently load app environment hooks from package metadata. → Move the hook to a Wevra default or explicit config-source selection before removing the app hook.
- [Risk] Some module settings may still be implicitly read through app `Settings`. → Audit imports and force settings reads through config services or module-owned public APIs.
- [Risk] Removing fallback defaults can expose incomplete local config. → Treat that as desired fail-fast behaviour and improve diagnostics rather than adding fallback.
- [Risk] `envex` may still provide useful dotenv/encrypted-env behaviour. → Keep it inside Wevra only when there is an actual requirement for that behaviour.

## Migration Plan

1. Audit app configuration, environment, settings, validation, and startup files and classify each concern as app-owned, Wevra-owned, module-owned, or removable.
2. Move reusable environment source/loading support into Wevra, preserving only required behaviours.
3. Move reusable config field definitions into Wevra or the module that owns each setting.
4. Replace app aggregation of module settings with module-owned loaders/capabilities.
5. Remove app-owned environment/config adapter files once all call sites have moved.
6. Update app tests to assert pristine app composition and optional module absence.
7. Update Wevra/module tests to cover moved config/environment behaviour.

## Open Questions

- Does Wevra still require `envex` encrypted dotenv support, or can the environment layer be simplified further?
- Which app settings are genuinely product-specific after database, auth, static, template, and validation concerns move out?
