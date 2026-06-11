## Context

`refactor-config-source` centralises loaded configuration in `wevra.config`, but the current host app settings object still aggregates module-owned typed settings. In particular, `app.settings.Settings` carries Wevra auth `IdentityOptions`, which makes the app aware of dependency internals and encourages app tests to assert dependency behaviour.

The better boundary is a shared raw configuration service plus module-owned typed settings. The host app should construct the central config service during startup, retain only host-owned settings in its own settings object, and let modules build or retrieve their own typed settings through module-owned loaders/accessors.

Constraints:

- Keep configuration source loading synchronous and startup-oriented.
- Keep raw config loading in `wevra.config`; do not add async subscriptions or dynamic config mechanics here.
- Do not add runtime dependencies or framework structure beyond what the refactor needs.
- Keep app tests focused on host-owned wiring; dependency settings behaviour belongs in the owning module's tests.

## Goals / Non-Goals

**Goals:**

- Split host-owned app settings from module-owned dependency settings.
- Define typed settings ownership and, if needed, a small `get_settings(owner)` provider protocol for cross-module typed settings access.
- Let each module expose its own typed settings object and loader/accessor.
- Treat module settings objects as immutable typed policy objects that may expose owner-specific behaviour as methods.
- Move Wevra auth typed settings access behind `wevra.auth` rather than `app.Settings.identity_options`.
- Preserve existing operator-facing configuration semantics while changing ownership boundaries.
- Preserve explicit host app settings construction for specialised tests and callers.

**Non-Goals:**

- Do not replace the central `ConfigService` model from `refactor-config-source`.
- Do not introduce dynamic config subscriptions, reload listeners, or async readiness.
- Do not force modules to depend on host app settings objects.
- Do not move module-specific coercion and policy validation into the raw config loader.
- Do not redesign unrelated authentication, persistence, or route composition behaviour.

## Decisions

### 1. Use module-owned settings loaders instead of an app-wide aggregate settings object

Modules that need configuration should own a loader/accessor that converts raw config into typed, validated settings. The raw configuration service remains `get_config(section_header) -> Mapping | None`; typed settings access, if centralised for cross-module use, should use separate terminology such as `get_settings(owner) -> typed settings`.

Rationale: this preserves a single loaded config source of truth without making the host app the owner of every module's typed settings.

Alternative considered: keep expanding `app.settings.Settings` with dependency settings. Rejected because it bloats the host object, leaks module policy upward, and drives tests across ownership boundaries.

### 2. Typed settings belong to the owning module

Each module may expose a typed settings object and loader, for example `wevra.auth` owning auth settings and identity options construction. The loader reads raw config from the provider, applies defaults, performs module-specific coercion and validation, and returns the module-owned settings object.

Rationale: settings policy lives close to the module that uses it, and module tests can cover that policy without involving the host app.

Alternative considered: make `wevra.config` perform all coercion and validation centrally. Rejected because it would turn the raw config layer into a policy-heavy registry and create cross-module coupling.

### 3. Module settings are immutable policy objects

Module-owned settings objects should be deeply immutable at their public boundaries after construction. A frozen typed settings object can safely be shared by reference by a settings provider without returning defensive copies, provided that nested collections and nested settings values are also immutable.

Settings objects may expose methods when those methods represent owner-specific policy decisions, for example `auth_settings.is_totp_enabled()`. Cross-module callers should depend on the module's public settings type or on a narrower public protocol rather than inspecting raw config.

Rationale: behaviour on a settings object keeps policy interpretation in the owning module and avoids spreading raw flag checks through unrelated domains.

Alternative considered: expose only passive data fields. Rejected because it encourages repeated policy interpretation outside the owning module.

Typed settings immutability is intentionally stricter than raw config immutability. Raw config preserves source values and freezes the section mapping boundary; typed settings loaders should normalise mutable values into immutable public forms, such as tuples, frozensets, mapping proxies, frozen dataclasses, or frozen Pydantic-style models.

### 4. Host app settings contain only host-owned runtime policy

`app.settings.Settings` should keep app-owned values such as deployment environment, app name, CSRF policy, database URL if host-owned, resource roots, static/template host settings, and any composition references the host itself needs. It should not carry `IdentityOptions` or future module settings unless the value is intentionally host-owned policy.

Rationale: the host app composes modules; it should not become the storage mechanism for dependency internals.

Alternative considered: preserve `identity_options` on app settings for convenience. Rejected as a transitional coupling that becomes worse as SMS, email code, passkey, and external provider settings grow.

### 5. Cross-module settings access goes through the owning module

If one module needs another module's settings, it should request them from the owning module's settings loader/accessor or depend on an explicit module-owned protocol. It should not reach through `app.Settings` to obtain another module's typed settings.

Rationale: this keeps ownership explicit and makes dependencies visible at the composition boundary.

Alternative considered: allow modules to inspect arbitrary config section headers directly. This remains possible for raw config, but typed settings should be acquired through the owner module to avoid duplicating validation and interpretation.

### 6. Treat section headers and settings owners as separate identifiers

A config section header identifies raw configuration shape, for example `app`, `app.static`, or `auth`. A settings owner identifies the module or domain responsible for typed settings, for example `app` or `wevra.auth`.

The initial owner set should be derived from the configured module list. A module may expose no settings loader if it has no typed settings. This avoids maintaining a second dynamic owner registry while preserving stricter domain boundaries.

### 7. Preserve central raw config and app startup ownership of source construction

The app and CLI continue to decide which config sources to load and when. The resulting `ConfigService` remains the shared substrate. This change adjusts typed settings ownership, not source discovery.

Rationale: the previous discussion already rejected self-describing config sources and async config loading as over-complex for current startup needs.

## Risks / Trade-offs

- Existing call sites may assume `settings.identity_options` exists. -> Migrate call sites to request auth settings from `wevra.auth` and keep a temporary compatibility path only if required by a staged migration plan.
- Moving settings ownership can expose hidden app tests that assert dependency behaviour. -> Move those assertions into Wevra tests and keep app tests focused on wiring outcomes.
- Multiple modules could duplicate raw parsing if they bypass owner loaders. -> Document and test the owner-loader pattern; prefer protocol-based typed access for cross-module needs.
- Composition code may need to pass both app settings and module settings during startup. -> Keep host app settings narrow and make module settings construction explicit in the composition layer.
- Database URL ownership may remain partly shared between app and migration/auth tooling. -> Treat database URL as host-owned composition config unless a module has an explicitly separate database boundary.

## Migration Plan

1. Identify current `app.Settings` fields that are host-owned versus module-owned.
2. Introduce module-owned settings loaders/accessors and add a small `get_settings(owner)` provider only if composition needs shared typed settings lookup.
3. Add module-owned typed settings loaders for existing dependency-owned settings, starting with Wevra auth.
4. Update app startup/composition to construct module settings from the central config service and pass them to module initialisation points.
5. Remove dependency-owned fields from `app.Settings` once call sites no longer require them.
6. Move tests for dependency settings semantics from app tests to the owning module's tests; leave app tests for host wiring and integration boundaries.
7. Validate full app and Wevra gates before review.

## Open Questions

- Should the settings provider protocol live in `wevra.config` or in a narrower composition module?
- Should module settings loaders be named consistently, for example `load_settings(config_provider)` or `settings_from_config(config_provider)`?
- Is a temporary compatibility property on `app.Settings` justified for staged migration, or should this be a direct breaking internal refactor?
