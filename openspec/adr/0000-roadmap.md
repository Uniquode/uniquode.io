# 0000: Roadmap

Date: 2026-06-16

Status: Living

## Purpose

This document records the current architecture-led roadmap for the project.

Unlike the numbered ADRs, this document is not a point-in-time decision record. It is intended to be updated as architecture decisions land, implementation progresses, and priorities change.

The roadmap should stay aligned with accepted and provisional ADRs, OpenSpec change status, and current implementation state.

## Current State

- ADR 0001 establishes the implementation platform.
- ADR 0002 establishes the runtime and deployment command conventions.
- ADR 0003 establishes CSS and theming conventions.
- ADR 0004 establishes the server-rendered UI delivery architecture.
- ADR 0005 establishes the identity and authentication architecture.
- ADR 0006 establishes the authorisation and access-control model.
- ADR 0007 reserves the future internal OAuth provider direction.
- ADR 0008 establishes media storage ownership and boundaries.
- Wybra is now the common application engine boundary. Host applications
  provide their FastAPI instance and product code; Wybra owns common startup,
  configured module setup, route/template/static discovery, middleware,
  validation, settings composition, and reusable capabilities.
- Site startup is based around a Wybra site object, configured modules, and
  capability registration.
- Module ordering is a precedence mechanism for routes, templates, static
  assets, and overrides. Capability dependencies should not use ordering as a
  dependency resolver.
- Lazy capability proxies are the intended dependency pattern where one module
  needs another module's capability at operation time.
- The current UI direction is server-rendered templates with selective dynamic
  enhancement.
- The current web foundation includes composed template/static lookup, route
  registration, staticfiles support, template context providers, CSRF support,
  security headers, error handling, and responsive/layout conventions.
- `wybra.widgets` owns optional reusable UI affordances such as theme selection
  and login/logout controls. Widget templates can override lower-level web
  defaults through normal module ordering.
- The current styling direction is Wybra-owned design tokens and plain CSS,
  with module/app override through template and static precedence.
- The current persistence direction is SQLAlchemy 2 async with Alembic,
  PostgreSQL in production, and SQLite for local/lightweight development and
  tests.
- The current identity direction is local-account-first, using FastAPI Users
  for baseline local account lifecycle and session-backed browser
  authentication, with reusable advanced identity features inside Wybra auth.
- The current access-control direction is group-, flag-, and scope-aware
  authorisation for pages, APIs, and administrative surfaces.
- The current profile/media direction is `wybra.profile` for app-facing user
  profile records and descriptors, backed by `wybra.media` for media storage,
  catalogue records, path/URL resolution, and optional media serving.
- The current generator direction is a `wybra-create` command family for
  creating sites and later application modules from Wybra-owned templates.
- The current static collection direction is a `wybra-collect` command that
  gathers configured module static assets for efficient external serving and
  optional processing.
- The current internal OAuth2 provider direction is deferred until a concrete
  API, federation, or delegated-access requirement exists. ADR 0007 reserves
  the future package and Authlib integration direction, with RS256/JWKS for JWT
  access and ID tokens and opaque server-stored refresh tokens by default.

The current immediate implementation item is the profile/media slice, including
media storage, profile records, profile image descriptors, and widget
integration.

A large incoming slice of work is the user-facing UI that stitches profile and
authentication options together: account/profile pages, authentication method
management, token management, verification flows, and related widgets or
partials.

## Near-Term Roadmap

### 1. Wybra Site Engine

- Keep host app boilerplate minimal: the app should focus on product routes,
  views, templates, and app-specific settings.
- Continue moving common FastAPI setup, module discovery, route/static/template
  composition, middleware, and validation into Wybra.
- Keep the site startup API simple and explicit.
- Keep `runserver` and ASGI loading aligned with project-root, config, database,
  and deployment-target command conventions.

### 2. Configuration and Validation

- Keep configuration module-owned through `ConfigDef`, `ConfigGroup`, and
  `ConfigField` style declarations.
- Keep host applications out of Wybra-owned environment, persistence, auth,
  static, and media configuration mechanics.
- Extend validation only for concrete app/module checks that catch broken
  routes, templates, static assets, media roots, persistence setup, and
  configured module resources before runtime.

### 3. Web Foundation and Widgets

- Continue consolidating reusable layout, context, staticfiles, template, and
  route behaviour into Wybra.
- Keep reusable optional UI behaviour in `wybra.widgets`.
- Preserve module/template override ordering so applications can replace
  defaults without special hooks.
- Add additional widgets only when a concrete reusable UX need exists.

### 4. Media and Profile

- Implement `wybra.media` as the reusable media storage boundary.
- Use `media.store(...)` as the common write contract for uploads, generated
  bytes, imports, and other stream-like sources.
- Store media item IDs in consuming modules.
- Implement `wybra.profile` for profile records, profile-picture media IDs, and
  profile image descriptors.
- Keep widgets consuming profile descriptors rather than auth or media internals.
- Build account/profile UI surfaces that compose profile details,
  profile-picture management, authentication options, and verification state.

### 5. Site and Module Generation

- Add the `wybra-create` command family.
- Start with `wybra-create site` for a minimal generated site matching the
  cleaned host-app shape.
- Leave the generator extensible for later module templates, including simple
  CRUD/data-management/report modules.
- Ensure generated sites demonstrate intended hooks without hiding meaningful
  code in package `__init__.py` files.

### 6. Static Collection and Asset Delivery

- Add `wybra-collect` to gather static assets from configured modules into a
  destination suitable for external serving.
- Preserve file metadata where practical.
- Keep room for configured processing steps such as Sass/SCSS compilation, CSS
  minification, and JavaScript minification when required.

### 7. Authorisation and Administration

- Continue implementing groups, scopes, flags, and administrative management
  through Wybra auth/authorisation capabilities.
- Keep page, route, and API access policy explicit and reusable.
- Add administration surfaces only behind the established access-control model.

### 8. Federation, Advanced Authentication, API, and OAuth2

- Establish API token support for machine access.
- Add user-facing API token creation, listing, revocation, and management UI.
- Add API surfaces for users, profiles, and media management once the
  corresponding capability contracts are stable.
- Add external identity linking and provider integration when concrete product
  requirements need it.
- Add passkeys, TOTP, recovery codes, and account-recovery policy in staged
  slices rather than as one large authentication rewrite.
- Verify TOTP end-to-end in the running application before layering further
  authentication-method UI on top of it.
- Extend authentication method management so users can inspect and manage
  available methods from account/profile surfaces.
- Reintroduce the internal OAuth provider boundary as an Authlib integration
  layer only when local users, authorisation scopes, and a concrete provider use
  case are ready.
- Keep provider enablement and public mount path host-owned, with issuer,
  audience, clients, scopes, consent, grants, token storage, and signing keys
  supplied by configuration or host interfaces.
- Clarify OAuth2 client integration boundaries for upstream providers.
- Align API and HTML surfaces around shared application services.

### 9. Public Pages and Content

- Introduce public page conventions.
- Decide whether any public content requires content-managed records with slugs.
- Keep content slugs in the domain layer rather than in route registration.

### 10. Background and Scheduled Work

- Introduce background execution for concrete product needs such as email
  delivery, verification expiry, cleanup, media processing, or scheduled
  maintenance.
- Support both one-shot background tasks and scheduled work.
- Define job execution, idempotency, observability, and failure handling when
  that requirement becomes real.

### 11. Email and Verification

- Add an email backend so signups, password reset, account verification, and
  notification flows can operate outside local-only development.
- Add email verification flows where required by account policy.
- Add phone verification only when a concrete product requirement needs phone
  numbers or SMS-capable identity checks.
- Keep verification policy owned by auth/account capabilities rather than by
  host app boilerplate.

## Working Principles

- Keep routes defined in code.
- Keep route naming stable and exportable.
- Keep page or content slugs in the relevant domain model.
- Keep HTML, partial, and API surfaces separate at the routing layer while sharing application services underneath.
- Keep module order as precedence, not dependency resolution.
- Keep capability dependencies lazy unless startup genuinely requires immediate
  failure.
- Keep absence as absence; do not invent fallback database, auth, media,
  profile, static, or module behaviour when something is not configured.
- Keep changes small and requirement-driven.

## Open Questions

- Whether route-manifest export should be JSON only, YAML only, or both.
- Whether user-defined flags should exist only on groups or also directly on users.
- Which external provider should be implemented first.
- Whether TOTP or WebAuthn/passkeys should be the next concrete advanced-auth
  feature.
- Which authentication method management UI should ship first after TOTP is
  verified end-to-end.
- Which Authlib primitives are sufficient for a later internal `auth_provider`
  implementation, if one is required.
- Whether the first OAuth provider implementation should support OAuth2 only or
  include OIDC discovery and ID tokens immediately.
- Whether public pages need content-management features early or can begin as static templates backed by application services.
- Whether media processing should remain an external processor pipeline or gain
  first-class Wybra processing abstractions.
- What minimum email backend abstraction is needed before signup and
  verification flows become useful.
- Whether background tasks should begin as an in-process scheduler/queue or
  immediately target an external worker system.
