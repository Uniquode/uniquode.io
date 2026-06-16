## 1. Lazy Capability Proxy Foundation

- [x] 1.1 Add a typed lazy capability proxy API to the site capability registry.
- [x] 1.2 Implement proxy binding on first required method use with cached successful resolution.
- [x] 1.3 Add explicit non-binding availability checks for optional capability use.
- [x] 1.4 Preserve immediate required capability lookup for startup-critical dependencies.
- [x] 1.5 Add tests proving module setup can create proxies before target capabilities are registered.
- [x] 1.6 Add tests proving missing proxied capabilities fail clearly at required use time without fallback behaviour.

## 2. Wevra Media Capability

- [x] 2.1 Create the `wevra.media` module structure and public media capability shape.
- [x] 2.2 Add Wevra-owned media configuration for media root, mount path, URL mode, and app-served media enablement.
- [x] 2.3 Add media catalogue model and migration with media ID, category, storage key, content type, size, and timestamps.
- [x] 2.4 Implement safe media key/path resolution under the configured media root.
- [x] 2.5 Reject unsafe media keys that escape the media root.
- [x] 2.6 Add category-aware storage key helpers, including profile hash-bucket key support.
- [x] 2.7 Resolve media URLs and internal paths from media IDs through the catalogue.
- [x] 2.8 Validate media root existence and writability before media write workflows use it.
- [x] 2.9 Add optional staticfiles-like serving for configured media files by storage key and app-served media item routes by ID where configured.
- [x] 2.10 Add media-owned storage workflow that writes the supplied stream, counts bytes, and registers the catalogue item.
- [x] 2.11 Add tests for media config loading, catalogue registration, upload storage, category key generation, ID URL/path resolution, traversal rejection, writability validation, and serving modes.

## 3. Wevra Profile Capability

- [x] 3.1 Create the `wevra.profile` module structure and public profile capability shape.
- [x] 3.2 Add profile persistence linked one-to-one with auth users without extending auth-owned tables.
- [x] 3.3 Add migrations for the initial profile table and profile-picture media ID reference.
- [x] 3.4 Add profile services for creating, retrieving, and updating profile records.
- [x] 3.5 Define the profile-owned image descriptor used by UI consumers.
- [x] 3.6 Implement profile image descriptor resolution using the media capability proxy and stored media ID.
- [x] 3.7 Add fallback profile image descriptor behaviour when no image media reference exists.
- [x] 3.8 Add tests for profile persistence, auth-user linkage, profile media ID storage, profile image descriptors, category key generation, and media proxy use.

## 4. Auth and Widget Boundary Updates

- [x] 4.1 Move the long-term profile image descriptor/helper ownership out of auth and into profile.
- [x] 4.2 Keep auth public APIs focused on current-user and identity resolution.
- [x] 4.3 Update the login widget context to consume profile-owned image descriptors when profile is available.
- [x] 4.4 Ensure the login widget renders acceptable authenticated output when profile is unavailable without calling auth-owned profile image helpers.
- [x] 4.5 Add tests for widgets consuming profile descriptors and for profile-absent rendering.

## 5. Configuration, Validation, and Examples

- [x] 5.1 Update application configuration examples to include the intended media/profile module configuration.
- [x] 5.2 Add media configuration validation for root, mount path, and serving options.
- [x] 5.3 Add profile validation for required table/migration and profile image descriptor resources.
- [x] 5.4 Ensure validation does not invent media/profile fallbacks when modules are absent.
- [x] 5.5 Formalise `media.store(...)` as the media-owned write contract for supplied byte streams.
- [x] 5.6 Add ADR documenting media storage boundaries, responsibilities, and `media.store(...)`.
- [x] 5.7 Update OpenSpec/ADR documentation if implementation reveals another architectural decision beyond this change.

## 6. Verification

- [x] 6.1 Run Wevra checks covering tests, linting, typing, validation, and dead-code checks.
- [x] 6.2 Run root application checks against the local workspace Wevra checkout; final root PR readiness still requires Wevra merged to `main`.
- [x] 6.3 Manually verify login widget rendering with profile absent, profile present without image, and profile present with media image where practical. Skipped by decision; fix later if breakage is found.
