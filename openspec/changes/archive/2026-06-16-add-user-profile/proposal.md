## Why

Linear: [UT-222](https://linear.app/uniquode/issue/UT-222/add-user-profile)

Reusable Wevra auth should stay focused on authentication, account state, and
identity lifecycle. Profile data belongs outside auth: a profile module should
own app-facing user profile records, profile-picture references, and profile UI
metadata without extending reusable auth tables.

Profile media also needs reusable writable storage and a durable catalogue.
That storage is not unique to profiles, so it should be provided by a shared
`wevra.media` module rather than by the app profile implementation itself.
Profile pictures then become one consumer of media storage, not the definition
of media storage.

The change also exposes a broader composition problem: module ordering is
currently at risk of constraining capability dependencies. Module order should
define precedence for routes, templates, static files, media overrides, and
similar surfaces. It should not force one module to appear before another only
so setup can eagerly resolve a dependency. Cross-module capability use should be
insulated from direct setup ordering through lazy capability proxies.

## What Changes

- Add a profile capability that owns user profile persistence, auth-user
  linkage, profile-picture references, and profile-image display descriptors.
- Move profile-image descriptor ownership out of auth and into profile so UI
  modules can ask profile how a user should be represented visually.
- Keep auth responsible for identity/current-user resolution only.
- Update widgets so the login control consumes profile image display data from
  profile when available instead of depending on auth-owned profile helpers.
- Add a reusable `wevra.media` capability/module for catalogue-backed writable
  media storage, safe path/key resolution, category-aware storage keys, and
  optional app-served media files.
- Formalise `media.store(...)` as the public write contract for media streams:
  callers provide a category, safe storage key, and async byte source, while
  media owns filesystem writing, byte counting, and catalogue registration.
- Store profile media references as media item IDs managed through
  `wevra.media` rather than storing uploaded image binary data or raw storage
  paths in the profile table.
- Store media catalogue entries with stable IDs, categories, storage keys,
  content metadata, and timestamps so other modules can refer to media items by
  ID while `wevra.media` owns path and URL resolution.
- Support category-structured storage keys so profile pictures and other media
  do not accumulate in a single directory.
- Resolve client-facing media URLs through `wevra.media` so deployments can use
  either app-served media or externally served filesystem paths without changing
  profile/widget consumers.
- Configure media through Wevra-owned media settings rather than app-specific
  profile settings, with paths resolved consistently from the loaded project
  configuration/root.
- Validate media root existence/writability before workflows that need writable
  media use it.
- Add a general lazy capability proxy model so modules can depend on capability
  shapes without eagerly binding to another module during setup.
- Preserve module ordering as a precedence mechanism, not a dependency
  availability mechanism.
- Leave room for future profile fields and future media processors without
  overfitting the initial schema or adding unnecessary runtime dependencies.
- Defer a public media/CDN strategy beyond local/simple app-served media until
  product requirements need it.

## Capabilities

### New Capabilities

- `user-profile`: Profile persistence, auth-user linkage, profile-picture
  reference storage, profile-image descriptor generation, and profile lifecycle
  policy.
- `media-storage`: Reusable media-root configuration, media item catalogue,
  category-aware storage-key/path resolution, writable storage expectations,
  and optional media file serving.
- `lazy-capability-proxy`: Typed capability proxies that expose the same public
  shape as the proxied capability, resolve on first meaningful use, cache the
  resolved capability, and fail clearly when a required capability is absent.

### Modified Capabilities

- `site-startup-api`: Add lazy capability proxy support and make capability
  dependency binding independent of module setup order except for genuinely
  startup-critical dependencies.
- `web-widgets`: Consume profile-owned profile-image descriptors for login
  widget avatar data when profile is available.
- `auth`: Remove long-term ownership of profile-image descriptor generation;
  auth remains the source of authenticated user identity only.
- `environment-configuration`: Add Wevra-owned media configuration and
  validation behaviour.

## Impact

- Affects Wevra site capability registration/resolution, profile and media
  module design, media catalogue migrations, auth/profile/widget boundaries,
  settings, configuration examples, validation, and future profile
  routes/templates.
- Keeps Wevra auth reusable by linking profile data to auth users rather than
  extending auth-owned tables.
- Reduces brittle module ordering constraints by treating ordering as
  precedence, while lazy capability proxies handle cross-module use.
- Adds no new runtime dependency unless later design work identifies a concrete
  image-processing or storage requirement.
