## 1. Public startup API

- [x] 1.1 Define the public Wevra startup entry point that accepts an existing FastAPI app and explicit config source input.
- [x] 1.2 Define the public `Site` type returned by startup.
- [x] 1.3 Add startup error handling for missing or failed config sources using existing configuration error types.
- [x] 1.4 Export the startup API and `Site` type from the intended public Wevra package path.
- [x] 1.5 Parse string config sources as local file paths or local `file://` URIs and reject unsupported source strings clearly.

## 2. Type-keyed site capabilities

- [x] 2.1 Add `SiteCapabilityError` for capability registration and lookup failures.
- [x] 2.2 Add `Site.provide_capability(capability_type, value)` keyed by capability type.
- [x] 2.3 Add `Site.require_capability(capability_type)` that returns the correctly typed capability or raises.
- [x] 2.4 Add `Site.has_capability(capability_type)` for explicit optional behaviour checks.
- [x] 2.5 Reject duplicate capability providers clearly.
- [x] 2.6 Reject capability values that do not satisfy the supplied capability type where runtime validation is possible.
- [x] 2.7 Add Wevra tests for capability registration, required lookup, missing capability failure, duplicate failure, and type mismatch failure.

## 3. Module setup lifecycle

- [x] 3.1 Define async `setup_site(site)` as the only configured module setup hook.
- [x] 3.2 Discover `setup_site` on configured module package roots.
- [x] 3.3 Invoke async `setup_site(site)` hooks in configured module order during Wevra startup.
- [x] 3.4 Ignore modules that do not expose `setup_site`.
- [x] 3.5 Fail startup clearly when `setup_site` exists but is not callable.
- [x] 3.6 Fail startup clearly when `setup_site` exists but is not async.
- [x] 3.7 Fail startup clearly when a module setup hook raises.
- [x] 3.8 Add Wevra tests for setup order, no-hook modules, invalid hooks, sync-hook rejection, and hook failures.

## 4. Database capability

- [x] 4.1 Define a public `DatabaseCapability` protocol or class.
- [x] 4.2 Provide `session(name="default")` as an async context manager for clean sessions.
- [x] 4.3 Provide `transaction(name="default")` as an async context manager for transactional work.
- [x] 4.4 Model named connections for `default`, `reader`, and `writer`, initially mapping names to one configured database when only one URL exists.
- [x] 4.5 Fail clearly for unknown connection names.
- [x] 4.6 Register `DatabaseCapability` from `wevra.db.setup_site(site)`.
- [x] 4.7 Move Wevra-owned database runtime setup out of the host app.
- [x] 4.8 Add Wevra tests for capability registration, session isolation, transaction commit/rollback, and unknown connection names.

## 5. Auth capability

- [x] 5.1 Define a public `AuthCapability` protocol or class.
- [x] 5.2 Implement `wevra.auth.setup_site(site)`.
- [x] 5.3 Require `DatabaseCapability` from auth setup.
- [x] 5.4 Initialise auth runtime settings, identity delivery, and FastAPI Users integration inside Wevra auth.
- [x] 5.5 Register `AuthCapability` from auth setup.
- [x] 5.6 Expose public auth helpers such as login-required and superuser dependencies through `AuthCapability`.
- [x] 5.7 Move auth route setup into Wevra startup composition.
- [x] 5.8 Remove host app `_configure_identity` and direct auth runtime construction.
- [x] 5.9 Add tests for auth setup with DB capability, missing DB capability failure, omitted auth module, and login route availability through unified web composition.

## 6. Route, template, and static setup

- [x] 6.1 Move configured module route registration behind Wevra startup.
- [x] 6.2 Move route-prefix handling for Wevra modules into Wevra startup.
- [x] 6.3 Remove host app Wevra route discovery and route-prefix fallback code.
- [x] 6.4 Move common template/static package-resource composition into Wevra where it is framework-owned.
- [x] 6.5 Keep host app route/template/static behaviour only where it is product-owned.
- [x] 6.6 Add tests for configured route registration, omitted modules, route prefixes, and resource composition.

## 7. Host app migration

- [x] 7.1 Update the host app to construct its FastAPI instance with `lifespan=wevra.start_site(config_source=...)`.
- [x] 7.2 Remove app-side Wevra database setup.
- [x] 7.3 Remove app-side Wevra auth setup.
- [x] 7.4 Remove app-side Wevra route discovery/setup.
- [x] 7.5 Replace app access to Wevra internals with public capabilities.
- [x] 7.6 Keep app-owned pages, routes, and product behaviour in the app.
- [x] 7.7 Add host app integration tests for startup, app-owned routes, configured auth login route, and static/template behaviour.

## 8. Test ownership cleanup

- [x] 8.1 Add initial Wevra tests for startup composition with an existing FastAPI app.
- [x] 8.2 Move framework startup semantics tests into Wevra tests.
- [x] 8.3 Remove host app tests that assert Wevra auth/database/route internals.
- [x] 8.4 Keep host app tests focused on app-owned behaviour and public startup integration.
- [x] 8.5 Remove tests for old startup paths rather than preserving compatibility expectations.

## 9. Documentation and examples

- [x] 9.1 Document the startup shape: `app = FastAPI(lifespan=wevra.start_site(config_source="app.toml"))`.
- [x] 9.2 Document `setup_site(site)` for modules.
- [x] 9.3 Document type-keyed capabilities with `DatabaseCapability` and `AuthCapability` examples.
- [x] 9.4 Document host-owned versus Wevra-owned boundaries.
- [x] 9.5 Document that legacy app-side Wevra startup is not supported.

## 10. Configured module surface composition correction

- [x] 10.1 Remove the host-route-module exclusion marker and any host route registration escape hatch added during implementation.
- [x] 10.2 Make Wevra discover and register `module_routers` for every configured module in `modules` order.
- [x] 10.3 Move auth route registration out of `wevra.auth.setup_site(site)` or otherwise ensure auth routes participate in the single configured route composition pass.
- [x] 10.4 Change route composition from fatal duplicate detection to first-module-wins duplicate handling for normalised method/full-path collisions.
- [x] 10.5 Log a structured warning when a later route is skipped because an earlier configured module already owns the method/full-path pair.
- [x] 10.6 Confirm template and static composition use first-module-wins precedence and document any existing shadow diagnostics.
- [x] 10.7 Remove app-side `register_routes(app)` startup calls; the app should expose route surfaces only.
- [x] 10.8 Add Wevra tests for configured module route order, app-overrides-Wevra route shadowing, duplicate-route warning, and auth routes through the unified route composition pass.
- [x] 10.9 Update host app tests to assert public behaviour from module-order composition rather than manual route registration.
- [x] 10.10 Treat `[app.routes]` as the publication allow-list for route surfaces, so unlisted discovered `module_routers` labels are not registered.
- [x] 10.11 Keep unknown configured route surface labels as explicit route composition errors.
- [x] 10.12 Add Wevra tests for unpublished route surfaces, unpublished modules, and unknown published route labels.
