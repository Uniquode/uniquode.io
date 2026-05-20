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
- The next immediate implementation item remains the `runserver` command baseline.
- The current UI direction is server-rendered templates with selective dynamic enhancement.
- The current styling direction is Pico CSS with a thin project-specific layer and planned theme support.
- The current identity direction is local-account-first, with linked external identities.
- The current access-control direction is group-, flag-, and scope-aware authorisation for pages, APIs, and admin surfaces.

## Near-Term Roadmap

### 1. Runtime Baseline

- Add the `runserver` project script defined by ADR 0002.
- Confirm the default local runtime behaviour, including host, port, and reload expectations.
- Add focused smoke coverage for application startup where practical.

### 2. Web Foundation

- Establish Jinja2 template environment conventions.
- Define base layouts, template naming, and static asset conventions.
- Establish the Pico CSS integration and project override conventions.
- Define the initial theme-mode behaviour for `auto`, `light`, and `dark`.
- Define `htmx` partial rendering conventions and response boundaries.
- Introduce route metadata conventions, including stable route names and identifiers.
- Add a route-manifest export mechanism for management, inspection, or tooling use.

### 3. Identity Foundation

- Introduce the local user account model.
- Add session-backed browser authentication.
- Define account bootstrap for the initial administrative user.
- Establish password-based local login flows.
- Reserve extension points for passkeys, TOTP, and external identity linking.

### 4. Authorisation Foundation

- Introduce groups as capability containers.
- Introduce group flags for gating behaviour, and decide whether direct user flags are also needed.
- Define route-, page-, and API-level access policy attachment.
- Provide administrative management of user membership, roles, and flags.

### 5. Federation and Advanced Authentication

- Add the external identity model and linking flows.
- Implement the first provider integration.
- Add provider-based account creation rules.
- Add passkey support.
- Add TOTP support.

### 6. API and OAuth2

- Establish API token support for machine access.
- Clarify the local OAuth2 authorisation-server capability boundary.
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
- How much OAuth2 authorisation-server capability is required in the first implementation slice.
- Which external provider should be implemented first.
- Whether public pages need content-management features early or can begin as static templates backed by application services.
