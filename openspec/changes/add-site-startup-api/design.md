## Context

Host applications currently construct and initialise Wevra-owned concerns directly: auth runtime state, module route registration, database configuration, settings access, and selected framework helpers. That makes each app repeat framework boilerplate and gives the app too much knowledge of Wevra internals.

The intended boundary is that a host app may own the `FastAPI()` instance for flexibility, then ask Wevra to compose the configured site from an explicit config source. After startup, the app should focus on product-owned pages, routes, and behaviour.

This change builds on the central configuration service and module-owned settings model. Configuration remains raw until consumed by owning modules; typed settings and helper capabilities are exposed by the owning Wevra module.

## Goals / Non-Goals

**Goals:**

- Provide a public startup API that composes Wevra into an existing FastAPI app.
- Return a `Site` object that exposes safe public settings and module capabilities.
- Move common module, auth, database, route, settings, and helper initialisation into Wevra.
- Keep app code free of Wevra-owned manipulation, defaults, environment handling, and runtime object construction.
- Preserve host-app control over FastAPI construction and app-owned routes.

**Non-Goals:**

- Do not make Wevra the only way to construct a FastAPI instance.
- Do not introduce dynamic configuration subscriptions or background config watching.
- Do not add compatibility paths that continue old app-side initialisation indefinitely.
- Do not require app code to inspect module internals to determine whether auth or other features are enabled.
- Do not add runtime dependencies unless implementation exposes a concrete requirement.

## Decisions

### `start()` composes an existing FastAPI app

Wevra will expose a startup entry point shaped like:

```python
site = wevra.start(app, config_source="app.toml")
```

The host app keeps ownership of the `FastAPI()` object. This preserves control over app metadata, middleware, exception handlers, lifespan, docs URLs, instrumentation, and deployment wrappers.

Alternative considered: `app = wevra.create_app(...)`. This is useful as a convenience later, but it makes Wevra the owner of the FastAPI constructor and reduces host flexibility. The primary API should accept an existing app.

### Startup returns a `Site` object

`start()` will return a `Site` object rather than a raw settings object or an unstructured runtime dictionary. `Site` represents the configured Wevra-backed web site and is the public place for host code to access module settings, dependencies, helpers, and capabilities.

Alternative considered: returning `AppSettings`. That would invite host apps to inspect central settings and make cross-module decisions themselves, recreating the boundary problem.

### Modules own their settings and capabilities

Configured modules will expose composition hooks and public capabilities through Wevra-owned interfaces. Auth, database, routes, and module settings remain owned by their modules. The host app asks `Site` for public helpers rather than constructing or mutating those internals.

Alternative considered: keeping helper construction in the host app and only centralising config. That still requires every app to repeat framework startup code and understand Wevra internals.

### Config source is injected into startup

The app or CLI resolves the config source before calling Wevra startup. `start()` accepts that explicit source and constructs the central configuration service from it.

CLI arguments that affect FastAPI constructor options remain host-owned because they are needed before the `FastAPI()` instance exists. CLI arguments that represent config overrides are passed to Wevra startup as explicit config inputs.

### No fallback feature inference from module names

Wevra startup determines what to compose from central config and module-owned configuration, not app-side hard-coded module checks. For example, auth composition is driven by the auth module/config boundary rather than by the host app testing for `"wevra.auth"`.

## Risks / Trade-offs

- [Risk] Moving composition into Wevra creates a larger public API surface. → Mitigation: keep `Site` small, typed, and capability-oriented; avoid exposing internal state directly.
- [Risk] Host apps may still need specialised startup hooks. → Mitigation: allow the host to own `FastAPI()` and provide app-owned routes or middleware before or after `start()`.
- [Risk] Module composition ordering can become implicit. → Mitigation: derive ordering from the configured module list and document module hook execution semantics.
- [Risk] Existing app tests may duplicate Wevra behaviour during migration. → Mitigation: move framework semantics into Wevra tests and keep app tests focused on app-owned integration.
- [Risk] Removing app-side initialisation is a breaking change. → Mitigation: migrate host code in the same change and keep the replacement API explicit and small.

## Migration Plan

1. Add the Wevra `start()` entry point and `Site` type.
2. Add module composition hooks for existing Wevra-owned concerns.
3. Move auth, database, route, and module settings initialisation behind Wevra startup.
4. Update the host app to construct `FastAPI()` and call `site = wevra.start(...)`.
5. Replace app-side Wevra helper construction with `Site` access where the app needs public dependencies or helpers.
6. Remove app tests that assert Wevra internals and add Wevra tests for startup composition.

Rollback is to restore the previous host-app startup wiring and remove the `Site` API usage from the host app. Because this change is explicitly breaking, rollback should happen as a normal code revert rather than by keeping compatibility initialisation paths.

## Open Questions

- What exact module hook name should Wevra use for composition: `module_site`, `compose_site`, `module_start`, or another concise convention?
- Should `Site.require(...)` return module capabilities by owner only, or should capabilities have separate names within an owner?
- Should `Site` expose typed settings directly through `get_settings(owner, type_)`, or should settings access always travel through owner-specific capability objects?
