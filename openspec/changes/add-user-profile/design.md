## Context

Wevra auth currently owns identity and account concerns. The next profile work
needs app-facing profile data, including profile-picture references, without
turning auth into a general user-profile module. Widgets also need a stable way
to render user-facing profile image data for the login/logout control without
binding directly to auth internals.

Media storage is broader than profile pictures. Profile images are only one
consumer of writable media, so media storage should be a reusable Wevra module
with its own capability, configuration, database catalogue, validation, and
simple serving support.

The profile/media relationship exposes a composition concern: modules are
configured in an ordered list, but that order should define precedence, not
cross-module dependency availability. Routes, templates, static files, and
similar surfaces can use ordering to decide winners. Capabilities should not
force modules to appear earlier only so another module can eagerly resolve them
during setup.

## Goals / Non-Goals

**Goals:**

- Add a profile capability that owns app-facing user profile records and
  profile-picture references linked to auth users.
- Add a reusable `wevra.media` capability for catalogue-backed media items,
  writable media roots, safe media keys/paths, categories, and optional local
  media serving.
- Move profile-image display descriptors out of auth and into profile.
- Let widgets consume profile image descriptors without knowing where image
  data is stored or how it is resolved.
- Introduce typed lazy capability proxies so cross-module dependencies bind on
  first meaningful use instead of during module setup.
- Preserve module ordering for precedence while avoiding artificial dependency
  ordering constraints.

**Non-Goals:**

- Do not add image processing, thumbnail generation, CDN integration, object
  storage, or external media dependencies in this change.
- Do not store uploaded image binary data in the database.
- Do not extend Wevra auth tables with app-owned profile fields.
- Do not introduce compatibility shims for old profile-image helper locations.
- Do not make module ordering a general dependency graph resolver.

## Decisions

### Profile owns profile display data

`wevra.profile` owns the public profile image descriptor used by UI consumers.
The descriptor should represent what a template needs to render an image or
fallback avatar, for example `src`, `alt`, and `fallback_text`.

Auth remains responsible for current-user identity. Profile receives an auth
user or user identifier and returns app-facing profile data. Widgets depend on
that profile descriptor rather than auth-specific helper functions.

Alternative considered: keep the initial `profile_image_for_user()` helper in
auth. Rejected because it gives auth ownership of profile presentation and
would make profile a later migration rather than the real boundary.

### Media is a reusable catalogue-backed Wevra module

`wevra.media` owns writable media storage and the media item catalogue, not
`wevra.profile` and not the host app. It provides stable media IDs,
category-aware storage keys, safe key/path resolution under a configured media
root, content metadata, validates writable storage when media workflows require
it, and can expose a simple local media file server for deployments that do not
serve media outside the ASGI app.

The public write contract is `media.store(...)`. Callers provide a category,
a safe storage key, and an async byte source. Media validates writable storage,
creates any required parent directories under the media root, streams bytes to
the resolved path, counts the stored bytes, records content metadata, and
registers the catalogue item. The caller stores the returned media ID. This
keeps upload, generated-file, and future stream-based workflows behind the same
media-owned boundary instead of making each consuming module manually write
files and then register them.

Profile stores media item IDs managed through `wevra.media`. Profile does not
store raw filesystem paths, does not invent storage keys itself except through
profile-owned naming policy, and does not create a fallback media store.

Alternative considered: profile stores raw relative media paths directly.
Rejected because modules should refer to media items by stable media ID while
`wevra.media` owns catalogue metadata, path resolution, and serving policy.

Alternative considered: expose only a catalogue `register(...)` API and require
callers to write files themselves. Rejected because media storage correctness
belongs to media; otherwise every consuming module must duplicate root
validation, safe path use, directory creation, size counting, and write/register
ordering.

### Media categories structure storage keys

Media items include a category such as `profile`, `reports`, or another
module-owned namespace. Categories prevent one flat media directory and give
modules a predictable place to apply storage policy.

The initial profile picture category is `profile`. Profile picture storage keys
should use deterministic hash-bucketed paths derived from the user ID, for
example `profile/8e/f0/<user-id>.png`. The original filename must not define
the storage path.

Alternative considered: put every file directly under the media root. Rejected
because large flat directories do not scale and make ownership less clear.

### Media URL resolution supports app and external serving

The media catalogue stores `id -> storage_key`. Public consumers ask
`wevra.media` for a URL or path for a media ID. The returned URL depends on
configuration:

- app-served ID mode can return `/media/items/<media-id>`;
- external/static serving mode can return `/media/<storage-key>`;
- internal file serving can call `path_for(media_id)` and return a file
  response.

The default should favour storage-key URLs for simple static/nginx serving,
while still allowing app-served ID routes when Wevra needs to mediate access.

Alternative considered: serve only by opaque media ID. Rejected because it
blocks direct nginx/static serving of the media root.

### Capability dependencies are lazy by default

Modules register their own capabilities during setup. When a module needs
another capability, it should depend on a typed proxy with the same public shape
as the target capability. The proxy is cheap to construct, resolves the real
capability on first meaningful use, caches a successful resolution, and raises a
clear capability error if required use occurs while the capability is absent.

Optional behaviour should use explicit non-binding availability checks exposed
by the proxy or site capability API. Required operations should fail clearly at
operation boundaries rather than during unrelated startup work.

Alternative considered: eager `site.require_capability(...)` calls in module
setup. Rejected because this makes module order artificially constrain
cross-module use and creates brittle ordering problems as capabilities grow.

### Module order remains precedence only

The configured module order continues to define deterministic precedence for
surfaces where ordering matters: routes, templates, static files, media
resolution precedence where applicable, and duplicate/override handling.

Capability dependency availability should not depend on that order except for
rare startup-critical dependencies genuinely required to register the module
itself. Profile can be configured before media and still register its own
capability; media-dependent methods fail only if they are used before a media
capability exists or when no media capability exists at all.

Alternative considered: introduce a two-phase setup dependency resolver now.
Rejected because lazy capability proxies solve the immediate binding problem
without adding dependency graph machinery.

### Media serving is simple and optional

`wevra.media` should provide a staticfiles-like media server for local and
simple deployments. This is a convenience path, not the only serving strategy.
Configuration should allow deployments to disable app-served media and serve
the media root externally later.

Alternative considered: defer media serving entirely. Rejected because profile
pictures need a concrete local development path and parity with static-file
style serving is straightforward.

## Risks / Trade-offs

- Lazy proxies can defer missing-capability failures until request time -> use
  clear capability errors and explicit availability checks for optional UI
  branches.
- Same-shape proxies can duplicate method declarations -> keep capability
  protocols small and focused so proxy implementations remain maintainable.
- Media path handling can introduce path traversal risk -> resolve and validate
  all media keys under the configured media root and reject unsafe paths.
- Local ASGI media serving may not be appropriate for production -> make serving
  configurable and keep the media root usable by external servers.
- Profile and media migrations introduce persistent schema/storage changes ->
  keep the initial schema minimal and avoid irreversible storage assumptions.

## Migration Plan

1. Add lazy capability proxy support to site capability APIs and tests.
2. Add `wevra.media` configuration, capability, validation, and simple media
   serving support.
3. Add `wevra.media` catalogue models and migrations before consumers store
   media item IDs.
4. Add `wevra.profile` models, migrations, capability, and profile image
   descriptor ownership.
5. Move profile-image descriptor resolution from auth to profile without keeping
   a compatibility shim.
6. Update widgets to use profile-owned descriptors when available.
7. Update app configuration examples and validation so media/profile behaviour
   is explicit. Root app work may proceed against the local workspace Wevra
   checkout during development; before the root PR is considered CI-ready,
   Wevra must still be merged to `main` because root CI checks out Wevra `main`.

Rollback during development is source-only: remove the profile/media modules,
remove their migrations before release, and restore widgets to not request
profile descriptors.

## Open Questions

- What exact table and migration naming should `wevra.media` use for media
  catalogue records?
- What exact table and migration naming should `wevra.profile` use for profile
  records and profile-picture media IDs?
- Should the first media serving route default to `/media`, or should the mount
  path be mandatory in configuration?
- Should the profile image descriptor include dimensions or content type now, or
  defer those until image processing is introduced?
