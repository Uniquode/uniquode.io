## 1. Public startup API

- [x] 1.1 Define the public Wevra startup entry point that accepts an existing FastAPI app and explicit config source input.
- [x] 1.2 Define the public `Site` type returned by startup.
- [x] 1.3 Add startup error handling for missing or failed config sources using existing configuration error types.
- [x] 1.4 Export the startup API and `Site` type from the intended public Wevra package path.

## 2. Site capabilities and settings access

- [x] 2.1 Add `Site` accessors for configured module presence without requiring host apps to inspect raw config internals.
- [ ] 2.2 Add typed settings access or settings-backed capability access keyed by explicit owner identifiers.
- [ ] 2.3 Ensure settings returned through `Site` preserve module ownership and public immutability boundaries.
- [ ] 2.4 Add explicit failure behaviour for missing owners, missing settings, or missing capabilities.

## 3. Module composition lifecycle

- [ ] 3.1 Define the module composition hook or convention used by configured modules during site startup.
- [ ] 3.2 Invoke module composition hooks in configured module order.
- [ ] 3.3 Ensure modules without composition hooks continue to load without special handling.
- [ ] 3.4 Keep module imports side-effect safe during config definition and composition discovery.

## 4. Wevra-owned runtime initialisation

- [ ] 4.1 Move auth runtime initialisation behind Wevra startup.
- [ ] 4.2 Move database runtime wiring behind Wevra startup.
- [ ] 4.3 Move configured module route registration behind Wevra startup.
- [ ] 4.4 Move route-prefix and module route discovery defaults out of host app code.
- [ ] 4.5 Expose public auth dependencies or helpers through `Site` or an auth-owned capability.

## 5. Host app migration

- [ ] 5.1 Update the host app to construct its FastAPI instance and call Wevra startup.
- [ ] 5.2 Remove host app construction of Wevra auth settings, auth delivery, FastAPI Users objects, database runtime state, and module route defaults.
- [ ] 5.3 Replace host app access to Wevra-owned settings with `Site` or module-owned public helpers.
- [ ] 5.4 Keep host app code focused on product-owned pages, routes, templates, and behaviour.

## 6. Tests and validation

- [x] 6.1 Add Wevra tests for startup composition with an existing FastAPI app.
- [ ] 6.2 Add Wevra tests for `Site` settings and capability access.
- [ ] 6.3 Add Wevra tests for auth, database, and route composition through startup.
- [ ] 6.4 Remove or rewrite host app tests that duplicate Wevra-owned auth, database, settings, or route composition semantics.
- [ ] 6.5 Add host app integration tests that assert app-owned startup and product routes work through the public Wevra startup API.

## 7. Documentation and examples

- [ ] 7.1 Document the preferred startup shape: `app = FastAPI(...)` followed by `site = wevra.start(app, config_source=...)`.
- [ ] 7.2 Document which concerns remain host-owned and which concerns are Wevra-owned after startup.
- [ ] 7.3 Add a concise example for protecting a host app route through a public auth helper exposed by `Site`.
- [ ] 7.4 Document CLI argument handling for FastAPI constructor options versus Wevra config-source and config-override inputs.
