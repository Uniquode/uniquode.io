## Context

Host applications currently construct and initialise Wevra-owned concerns directly: auth runtime state, module route registration, database configuration, settings access, and selected framework helpers. That makes each app repeat framework boilerplate and gives the app too much knowledge of Wevra internals.

The intended boundary is that a host app may own the `FastAPI()` instance for flexibility, then ask Wevra to compose the configured site from an explicit config source. After startup, the app should focus on product-owned pages, routes, and behaviour.

This change builds on the central configuration service and module-owned settings model. Configuration remains raw until consumed by owning modules; typed settings and helper capabilities are exposed by the owning Wevra module.

## Goals / Non-Goals

**Goals:**

- Provide a public startup API that composes Wevra into an existing FastAPI app.
- Return a `Site` object that exposes safe public type-keyed capabilities.
- Move common module, auth, database, route, settings, and helper initialisation into Wevra.
- Keep app code free of Wevra-owned manipulation, defaults, environment handling, and runtime object construction.
- Preserve host app control over FastAPI construction and app-owned routes.

**Non-Goals:**

- Do not make Wevra the only way to construct a FastAPI instance.
- Do not introduce dynamic configuration subscriptions or background config watching.
- Do not add compatibility paths, legacy shims, or fallback behaviour for old app-side Wevra initialisation.
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

`start()` will return a `Site` object rather than a raw settings object or an unstructured runtime dictionary. `Site` represents the configured Wevra-backed web site and is the public place for host code and modules to access public type-keyed capabilities.

Alternative considered: returning `AppSettings`. That would invite host apps to inspect central settings and make cross-module decisions themselves, recreating the boundary problem.

### Modules own their settings and capabilities

Configured modules will expose one setup hook, `setup_site(site)`, and public capabilities through Wevra-owned interfaces. Auth, database, routes, and module settings remain owned by their modules. The host app asks `Site` for public capabilities rather than constructing or mutating those internals.

Alternative considered: keeping helper construction in the host app and only centralising config. That still requires every app to repeat framework startup code and understand Wevra internals.

### Config source is injected into startup

The app or CLI resolves the config source before calling Wevra startup. `start()` accepts that explicit source and constructs the central configuration service from it.

CLI arguments that affect FastAPI constructor options remain host-owned because they are needed before the `FastAPI()` instance exists. CLI arguments that represent config overrides are passed to Wevra startup as explicit config inputs.

### Module setup uses `setup_site(site)` only

Wevra startup calls a single optional module-root hook named `setup_site(site)` in configured module order. Modules without the hook are ignored, and invalid hooks fail startup clearly. There are no alternate hook names, compatibility aliases, or legacy startup paths.

### Capabilities are keyed by type

`Site` capabilities are looked up by public capability type rather than provider module name. Consumers request the contract they need, such as `DatabaseCapability` or `AuthCapability`, and do not care which module provided it. Missing or duplicate capabilities fail clearly. Optional behaviour uses `has_capability(...)` followed by `require_capability(...)`.

## Risks / Trade-offs

- [Risk] Moving composition into Wevra creates a larger public API surface. → Mitigation: keep `Site` small, typed, and capability-oriented; avoid exposing internal state directly.
- [Risk] Capability lookup could become a service locator. → Mitigation: key capabilities by public type, keep capability objects intentionally small, and use them only for module-owned runtime services.
- [Risk] Host apps may still need specialised startup hooks. → Mitigation: allow the host to own `FastAPI()` and provide app-owned routes or middleware before or after `start()`.
- [Risk] Module composition ordering can become implicit. → Mitigation: derive ordering from the configured module list and document module hook execution semantics.
- [Risk] Existing app tests may duplicate Wevra behaviour during migration. → Mitigation: move framework semantics into Wevra tests and keep app tests focused on app-owned integration.
- [Risk] Removing app-side initialisation is a breaking change. → Mitigation: this product is unreleased, so remove old ownership directly rather than carrying compatibility code.

## Migration Plan

1. Add the Wevra `start()` entry point and `Site` type.
2. Add the type-keyed capability registry.
3. Add the `setup_site(site)` module lifecycle.
4. Move database, auth, route, template, and static initialisation behind Wevra startup.
5. Update the host app to construct `FastAPI()` and call `site = wevra.start(...)`.
6. Remove old app-side Wevra initialisation and tests that assert removed internals.
7. Add Wevra tests for startup composition and host app tests for public startup integration.

Rollback is a normal code revert. No compatibility path or legacy fallback is kept.

## Open Questions

- Should `DatabaseCapability` be a runtime-checkable protocol or a concrete abstract base class for stricter runtime validation?
- Which route/template/static setup pieces belong in `wevra.web.setup_site(site)` versus generic Wevra startup?
