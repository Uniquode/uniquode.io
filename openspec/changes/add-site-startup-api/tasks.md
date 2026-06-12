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

- [x] 3.1 Define `setup_site(site)` as the only configured module setup hook.
- [x] 3.2 Discover `setup_site` on configured module package roots.
- [x] 3.3 Invoke `setup_site(site)` in configured module order during `wevra.start(...)`.
- [x] 3.4 Ignore modules that do not expose `setup_site`.
- [x] 3.5 Fail startup clearly when `setup_site` exists but is not callable.
- [x] 3.6 Fail startup clearly when a module setup hook raises.
- [x] 3.7 Add Wevra tests for setup order, no-hook modules, invalid hooks, and hook failures.

## 4. Database capability

- [ ] 4.1 Define a public `DatabaseCapability` protocol or class.
- [ ] 4.2 Provide `session(name="default")` as an async context manager for clean sessions.
- [ ] 4.3 Provide `transaction(name="default")` as an async context manager for transactional work.
- [ ] 4.4 Model named connections for `default`, `reader`, and `writer`, initially mapping names to one configured database when only one URL exists.
- [ ] 4.5 Fail clearly for unknown connection names.
- [ ] 4.6 Register `DatabaseCapability` from `wevra.db.setup_site(site)`.
- [ ] 4.7 Move Wevra-owned database runtime setup out of the host app.
- [ ] 4.8 Add Wevra tests for capability registration, session isolation, transaction commit/rollback, and unknown connection names.

## 5. Auth capability

- [ ] 5.1 Define a public `AuthCapability` protocol or class.
- [ ] 5.2 Implement `wevra.auth.setup_site(site)`.
- [ ] 5.3 Require `DatabaseCapability` from auth setup.
- [ ] 5.4 Initialise auth runtime settings, identity delivery, and FastAPI Users integration inside Wevra auth.
- [ ] 5.5 Register `AuthCapability` from auth setup.
- [ ] 5.6 Expose public auth helpers such as login-required and superuser dependencies through `AuthCapability`.
- [ ] 5.7 Move auth route setup into Wevra auth.
- [ ] 5.8 Remove host app `_configure_identity` and direct auth runtime construction.
- [ ] 5.9 Add tests for auth setup with DB capability, missing DB capability failure, omitted auth module, and login route availability.

## 6. Route, template, and static setup

- [ ] 6.1 Move configured module route registration behind Wevra startup.
- [ ] 6.2 Move route-prefix handling for Wevra modules into Wevra startup.
- [ ] 6.3 Remove host app Wevra route discovery and route-prefix fallback code.
- [ ] 6.4 Move common template/static package-resource composition into Wevra where it is framework-owned.
- [ ] 6.5 Keep host app route/template/static behaviour only where it is product-owned.
- [ ] 6.6 Add tests for configured route registration, omitted modules, route prefixes, and resource composition.

## 7. Host app migration

- [ ] 7.1 Update the host app to construct its FastAPI instance and call `site = wevra.start(app, config_source=...)`.
- [ ] 7.2 Remove app-side Wevra database setup.
- [ ] 7.3 Remove app-side Wevra auth setup.
- [ ] 7.4 Remove app-side Wevra route discovery/setup.
- [ ] 7.5 Replace app access to Wevra internals with public capabilities.
- [ ] 7.6 Keep app-owned pages, routes, and product behaviour in the app.
- [ ] 7.7 Add host app integration tests for startup, app-owned routes, configured auth login route, and static/template behaviour.

## 8. Test ownership cleanup

- [x] 8.1 Add initial Wevra tests for startup composition with an existing FastAPI app.
- [ ] 8.2 Move framework startup semantics tests into Wevra tests.
- [ ] 8.3 Remove host app tests that assert Wevra auth/database/route internals.
- [ ] 8.4 Keep host app tests focused on app-owned behaviour and public startup integration.
- [ ] 8.5 Remove tests for old startup paths rather than preserving compatibility expectations.

## 9. Documentation and examples

- [ ] 9.1 Document the startup shape: `app = FastAPI(...)` then `site = wevra.start(app, config_source="app.toml")`.
- [ ] 9.2 Document `setup_site(site)` for modules.
- [ ] 9.3 Document type-keyed capabilities with `DatabaseCapability` and `AuthCapability` examples.
- [ ] 9.4 Document host-owned versus Wevra-owned boundaries.
- [ ] 9.5 Document that legacy app-side Wevra startup is not supported.
