## 1. Ownership audit and public contracts

- [x] 1.1 Audit `app.settings.Settings` fields and classify each as host-owned, composition-owned, or module-owned.
- [x] 1.2 Identify current call sites that read dependency-owned settings through `app.Settings`.
- [x] 1.3 Define typed settings owner identifiers separately from raw config section headers.
- [x] 1.4 Decide the public naming convention for module-owned settings loaders, accessors, and immutable settings policy objects.

## 2. Module-owned settings loaders

- [x] 2.1 Add a Wevra auth-owned typed settings loader that reads auth config from the central provider.
- [x] 2.2 Ensure the auth settings loader applies auth-specific defaults, coercion, validation, and environment overrides close to auth use.
- [x] 2.3 Preserve existing auth operator-facing configuration semantics during the ownership move.
- [x] 2.4 Make auth-owned settings deeply immutable at public boundaries and expose owner-specific policy helpers where useful.
- [x] 2.5 Add tests in Wevra for auth-owned settings defaults, environment overrides, validation, deep immutability, policy helpers, and policy errors.

## 3. Host app settings boundary

- [x] 3.1 Refactor `app.Settings` so it contains only host-owned runtime policy and configuration.
- [x] 3.2 Remove dependency-owned settings fields from `app.Settings` once call sites are migrated.
- [x] 3.3 Preserve explicit construction of host-owned app settings for tests and specialised callers.
- [x] 3.4 Keep host-owned post-load coercion and validation in the app settings layer rather than in `wevra.config`.

## 4. Startup and composition migration

- [x] 4.1 Update app startup to construct the central config provider once and pass it to module settings loaders.
- [x] 4.2 Update auth composition to request auth settings from `wevra.auth` rather than from `app.Settings`.
- [x] 4.3 Update cross-module settings access to go through the owning module's loader, accessor, or protocol.
- [x] 4.4 Preserve app/CLI source injection boundaries established by `refactor-config-source`.

## 5. Test boundary cleanup

- [x] 5.1 Move dependency settings behaviour tests from app tests to the owning Wevra module tests where practical.
- [x] 5.2 Keep app tests focused on host-owned settings, startup wiring, and integration outcomes.
- [x] 5.3 Remove duplicated assertions that test Wevra settings semantics from the host app suite.
- [x] 5.4 Add or update integration tests proving app startup wires module settings correctly without aggregating them in `app.Settings`.

## 6. Validation

- [x] 6.1 Run Wevra lint, format, type, and full pytest gates.
- [x] 6.2 Run app lint, format, type, validation command, and full app pytest gates.
- [x] 6.3 Run OpenSpec validation for `refactor-app-settings`.
- [x] 6.4 Treat unexpected check failures as side effects unless verified against `main`.
