# 0008: Media Storage

Date: 2026-06-16

Status: Provisional

## Context

User profile work introduces profile pictures, but profile pictures are only
one example of application media. Reports, exports, user uploads, generated
documents, and future modules may also need writable media storage.

The project needs one clear ownership boundary so consuming modules do not
duplicate filesystem handling, path safety checks, byte counting, catalogue
registration, URL generation, or serving policy.

The application also needs to support different delivery modes:

- local development and simple deployments where Wevra serves media from the
  ASGI application;
- deployments where nginx or another external server serves media files
  directly from the filesystem;
- future workflows where media bytes come from HTTP uploads, generated content,
  imports, or other stream-like sources.

At the same time, reusable modules such as profile must not store raw
filesystem paths as their public media references. A profile should remember
which media item belongs to the user, while media owns where that item lives and
how it is exposed.

The project also needs a distinct `resources` category for mutable or frequently
updated reference data used across modules (for example, country codes,
regions, and state/province lists). These are not general media assets and should
not be exposed as raw media item IDs alone. They should be managed through
dedicated resource/configuration mechanisms so they can be validated, versioned,
and governed independently from binary media delivery.

## Decision

Create `wevra.media` as the reusable media boundary.

`wevra.media` owns:

- media-root configuration;
- media item catalogue records;
- media item IDs;
- category-aware storage keys;
- filesystem path safety checks;
- media file writing;
- byte counting;
- content metadata captured at storage time;
- path resolution;
- URL resolution;
- optional app-served media routes or staticfiles-like serving.

Modules that consume media store media item IDs, not raw filesystem paths and
not public URLs.

Use a media item catalogue to map:

```text
media_id -> category, storage_key, content_type, size, timestamps
```

Use media categories to divide storage ownership. For example, profile
pictures use the `profile` category and deterministic bucketed storage keys such
as:

```text
profile/8e/f0/<user-id>.png
```

The original uploaded filename must not define the storage path.

Formalise `media.store(...)` as the public media write contract. Callers provide
a category, a safe storage key, and an async byte source. `wevra.media` validates
the writable media root, resolves the safe path, creates required parent
directories, streams bytes to the file, counts the stored bytes, records content
metadata, and registers the catalogue item. The caller stores the returned media
ID.

Keep lower-level catalogue registration available only for cases where media is
already present under the managed media root and the caller deliberately needs
to attach a catalogue record to that existing file. Normal write workflows
should use `media.store(...)`.

Resolve media paths and URLs through `wevra.media`:

- `path_for(media_id)` resolves an internal filesystem path through the
  catalogue;
- `url_for(media_id)` resolves a client-facing URL according to configured
  serving mode;
- storage-key URL mode may return URLs such as `/media/<storage-key>` for
  external static serving;
- app-served ID mode may return URLs such as `/media/items/<media-id>` where
  Wevra resolves the ID before sending the file.

`wevra.profile` owns profile records and profile image descriptors. It may
derive a profile-specific storage key, call `media.store(...)`, and store the
returned media ID on the profile record. It must not write media files itself,
store raw media paths, or own media serving.

Define a dedicated `resources` category for module-shared reference data that needs
updates over time and cross-module availability. Resource ingestion may still use
`wevra.media` as a physical storage transport, but references should be explicit
and lookup-driven (for example, tagged by `resource_id` such as
`country-codes`) rather than relying on implicit path assumptions.

To support this, add media resource lookup semantics:

- `store_resource(...)` (or equivalent) to register a managed media entry with a
  stable resource key.
- `get_by_resource_id(resource_id: str) -> MediaItem | None` for consumers that
  need stable semantic lookup.

`wevra.widgets` consumes profile image descriptors only. It does not inspect
media storage, auth internals, or profile persistence.

Capability dependencies should use lazy capability proxies where module setup
order would otherwise create artificial constraints. Profile may hold a lazy
media capability proxy and resolve it only when media-backed profile image
operations are actually used.

Do not create fallback media storage. If `wevra.media` is absent, media-backed
operations are unavailable and should fail clearly when required.

## Consequences

Media storage behaviour is centralised in one reusable module instead of being
duplicated by profile, widgets, or the host application.

Consumers have stable media item IDs and do not need to know whether files are
served by Wevra, nginx, or another later mechanism.

The storage-key URL mode keeps direct static serving practical because the URL
can map directly onto a file under the media root.

The app-served ID mode keeps a path available for deployments that need Wevra to
mediate media lookup before sending a response.

`media.store(...)` gives uploads, generated files, imports, and future
stream-based workflows one consistent write path.

Profile remains an app-facing user-profile module and does not become a media
storage implementation.

Widgets remain presentation consumers and do not gain storage or identity
responsibilities.

Media path traversal risk is handled in one place, but that makes
`wevra.media` path validation and tests a security-critical boundary.

The media catalogue introduces a database dependency for catalogue-backed media
operations. That dependency should be resolved through site capabilities, with
lazy binding where ordering would otherwise constrain module setup.

## Non-Goals

- Do not add image processing, resizing, thumbnailing, virus scanning, CDN
  integration, object storage, or signed URL generation in this decision.
- Do not store media binary data in the database.
- Do not make profile or widgets responsible for filesystem writes.
- Do not use raw filesystem paths as the public reference between modules.
- Do not create implicit fallback media storage when `wevra.media` is not
  configured.
- Do not route mutable reference data (for example, country/state dictionaries)
  as untagged media paths; they require explicit resource registration and key
  lookup.

## Follow-Up Work

- Define any future media processing pipeline only when a concrete requirement
  exists.
- Define object storage or CDN support only when deployment requirements need
  it.
- Define access-controlled or private media serving separately if product
  requirements need media visibility rules.
- Define profile-picture upload routes and forms on top of the `media.store(...)`
  contract.
