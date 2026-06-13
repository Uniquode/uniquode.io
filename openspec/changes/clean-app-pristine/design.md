## Context

The host application still contains configuration and environment scaffolding that predates Wevra-owned startup, module setup, and config services. Files such as `config_definitions.py` and `environment.py` make the app responsible for concerns that now belong to Wevra or to configured modules.

The target shape is a pristine host app: app-owned routes, views, context, and product settings only. Generic environment loading, config definition handling, validation, module startup, database setup, auth setup, static/template composition, and route discovery belong inside Wevra or the module that owns the behaviour.

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

### Settings shrink to app-owned values

The host app `Settings` type will retain only values the product app actually owns. Module-owned settings will be loaded from the central config service by the owning module or through an explicit public capability/helper.

Alternative considered: retain bridged settings fields for startup convenience. That repeats the old coupling and blocks modules from being replaced by compatible capability providers, so it is rejected.

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
