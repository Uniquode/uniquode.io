# 000: Roadmap

Date: 2026-05-20

Status: Living

## Purpose

This document records the current architecture-led roadmap for the project.

Unlike the numbered ADRs, this document is not a point-in-time decision record. It is intended to be updated as architecture decisions land, implementation progresses, and priorities change.

The roadmap should stay aligned with accepted and provisional ADRs, OpenSpec change status, and current implementation state.

## Current State

- ADR 0001 establishes the implementation platform.
- ADR 0002 establishes the runtime and deployment command conventions.
- The `runserver` command baseline is implemented.
- The initial HTML-first web foundation is implemented, including:
  - configurable template and static roots
  - Pico CSS and `htmx` delivery
  - semantic theme handling for `auto`, `light`, and `dark`
  - explicit page, partial, API, and static route-surface separation
  - foundational error handling across those surfaces
- The current UI direction is server-rendered templates with selective dynamic enhancement.
- The current styling direction is Pico CSS with a thin project-specific layer and planned theme support.
- The current persistence direction is SQLAlchemy 2 async with Alembic, PostgreSQL in production, and SQLite for local/lightweight tests.
- The current identity direction is local-account-first, using FastAPI Users for baseline local account lifecycle work and reserving linked external identities.
- The current advanced-authentication direction is a standalone `fastapi-users-auth-ext` addon for TOTP, WebAuthn/passkeys, recovery codes, and MFA challenge flows.
- The current access-control direction is group-, flag-, and scope-aware authorisation for pages, APIs, and admin surfaces.
- The current internal OAuth2 provider direction is deferred until a concrete
  API, federation, or delegated-access requirement exists. ADR 0007 reserves
  `auth_provider` as the future package name and Authlib integration direction,
  with RS256/JWKS for JWT access and ID tokens and opaque server-stored refresh
  tokens by default.

The next immediate implementation item is the identity foundation slice.

## Near-Term Roadmap

### 1. Runtime Baseline

- Keep the `runserver` command and startup smoke coverage aligned with runtime changes.
- Extend runtime checks only when new operational requirements appear.

### 2. Web Foundation

- The first Jinja2, static asset, layout, component, theming, and route-surface conventions are in place.
- The foundational error-handling contract is in place for page, partial, API, and static surfaces.
- Continue this slice only for genuinely foundational gaps such as route-manifest export or other cross-cutting web-platform requirements.

### 3. Identity Foundation

- Introduce the local user account model.
- Move persistence from Tortoise ORM to SQLAlchemy async with Alembic.
- Add FastAPI Users for baseline local account lifecycle and authentication primitives.
- Add session-backed browser authentication.
- Define account bootstrap for the initial administrative user.
- Establish password-based local login flows.
- Reserve extension points for passkeys, TOTP, recovery codes, and external identity linking.
- Create the standalone `fastapi-users-auth-ext` package/module boundary for future advanced authentication.

### 4. Authorisation Foundation

- Introduce groups as capability containers.
- Introduce group flags for gating behaviour, and decide whether direct user flags are also needed.
- Define route-, page-, and API-level access policy attachment.
- Provide administrative management of user membership, roles, and flags.

### 5. Federation and Advanced Authentication

- Add the external identity model and linking flows.
- Implement the first provider integration.
- Add provider-based account creation rules.
- Add TOTP and WebAuthn/passkey support through `fastapi-users-auth-ext`.
- Add recovery-code and account-recovery policy.

### 6. API and OAuth2

- Establish API token support for machine access.
- Reintroduce the internal `auth_provider` package boundary as an Authlib
  integration layer only when local users, authorisation scopes, and a concrete
  provider use case are ready.
- Keep provider enablement and public mount path host-owned, with issuer,
  audience, clients, scopes, consent, grants, token storage, and signing keys
  supplied by configuration or host interfaces.
- Clarify OAuth2 client integration boundaries for upstream providers.
- Align API and HTML surfaces around shared application services.

### 7. Public Pages and Content

- Introduce public page conventions.
- Decide whether any public content requires content-managed records with slugs.
- Keep content slugs in the domain layer rather than in route registration.

### 8. Background and Scheduled Work

- Introduce background or scheduled execution only when a concrete requirement appears.
- Define job execution, idempotency, observability, and failure handling when that requirement becomes real.

## Working Principles

- Keep routes defined in code.
- Keep route naming stable and exportable.
- Keep page or content slugs in the relevant domain model.
- Keep HTML, partial, and API surfaces separate at the routing layer while sharing application services underneath.
- Keep changes small and requirement-driven.

## Open Questions

- Whether route-manifest export should be JSON only, YAML only, or both.
- How Pico should be packaged and whether any CSS asset build step is required.
- Whether user-defined flags should exist only on groups or also directly on users.
- Which external provider should be implemented first.
- Whether TOTP or WebAuthn/passkeys should be the first concrete feature in `fastapi-users-auth-ext`.
- Which Authlib primitives are sufficient for a later internal `auth_provider`
  implementation, if one is required.
- Whether the first OAuth provider implementation should support OAuth2 only or
  include OIDC discovery and ID tokens immediately.
- Whether public pages need content-management features early or can begin as static templates backed by application services.
