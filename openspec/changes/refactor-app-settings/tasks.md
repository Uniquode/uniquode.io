## 1. Ownership audit and public contracts

- [ ] 1.1 Audit `app.settings.Settings` fields and classify each as host-owned, composition-owned, or module-owned.
- [ ] 1.2 Identify current call sites that read dependency-owned settings through `app.Settings`.
- [ ] 1.3 Define or select the settings provider protocol shape based on `get_config(section)`.
- [ ] 1.4 Decide the public naming convention for module-owned settings loaders and accessors.

## 2. Module-owned settings loaders

- [ ] 2.1 Add a Wevra auth-owned typed settings loader that reads auth config from the central provider.
- [ ] 2.2 Ensure the auth settings loader applies auth-specific defaults, coercion, validation, and environment overrides close to auth use.
- [ ] 2.3 Preserve existing auth operator-facing configuration semantics during the ownership move.
- [ ] 2.4 Add tests in Wevra for auth-owned settings defaults, environment overrides, validation, and policy errors.

## 3. Host app settings boundary

- [ ] 3.1 Refactor `app.Settings` so it contains only host-owned runtime policy and configuration.
- [ ] 3.2 Remove dependency-owned settings fields from `app.Settings` once call sites are migrated.
- [ ] 3.3 Preserve explicit construction of host-owned app settings for tests and specialised callers.
- [ ] 3.4 Keep host-owned post-load coercion and validation in the app settings layer rather than in `wevra.config`.

## 4. Startup and composition migration

- [ ] 4.1 Update app startup to construct the central config provider once and pass it to module settings loaders.
- [ ] 4.2 Update auth composition to request auth settings from `wevra.auth` rather than from `app.Settings`.
- [ ] 4.3 Update cross-module settings access to go through the owning module's loader, accessor, or protocol.
- [ ] 4.4 Preserve app/CLI source injection boundaries established by `refactor-config-source`.

## 5. Test boundary cleanup

- [ ] 5.1 Move dependency settings behaviour tests from app tests to the owning Wevra module tests where practical.
- [ ] 5.2 Keep app tests focused on host-owned settings, startup wiring, and integration outcomes.
- [ ] 5.3 Remove duplicated assertions that test Wevra settings semantics from the host app suite.
- [ ] 5.4 Add or update integration tests proving app startup wires module settings correctly without aggregating them in `app.Settings`.

## 6. Validation

- [ ] 6.1 Run Wevra lint, format, type, and full pytest gates.
- [ ] 6.2 Run app lint, format, type, validation command, and full app pytest gates.
- [ ] 6.3 Run OpenSpec validation for `refactor-app-settings`.
- [ ] 6.4 Treat unexpected check failures as side effects unless verified against `main`.
