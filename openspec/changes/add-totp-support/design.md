## Context

The existing authentication ceremony boundary supports primary assertions plus
additional method steps before final browser session issuance.

TOTP should remain within this model as a standalone method that can be enabled,
enrolled, and required by policy.

## Goals / Non-Goals

**Goals:**

- Define TOTP requirements independently from provider and passkey slices.
- Preserve existing ceremony gating (`is_active`, expiry, and required-method policy).
- Define secret protection so plaintext seeds are never exposed outside enrolment/verification surfaces.

**Non-Goals:**

- Do not implement concrete third-party OAuth or WebAuthn code.
- Do not add runtime dependencies beyond what `add-totp-support` implementation requires.
- Do not redefine provider linking or external account creation policy.

## Decisions

### TOTP as a method assertion

TOTP is modelled as a method assertion that can satisfy a configured ceremony policy.
This keeps policy evaluation and session issuance in one place.

### Pending state before active state

TOTP enrolment should create a pending credential, and only a successful confirmation
turns it into an active credential for ceremony assertion.

### Replay and window as explicit security controls

Time-step windows and replay handling must be configurable by host policy. A narrow
default that favours security is preferred.

### Secret handling is sensitive-by-default

The TOTP seed contract should prevent passive disclosure in templates, logs,
and management data structures, while still allowing verification.

## Migration Plan

1. Create focused TOTP requirements (`specs/totp`).
2. Update `identity-authentication` and `fastapi-users-auth-ext` change sets to consume
   TOTP assertions when enabled.
3. Keep provider and passkey implementations untouched by this change.
4. Add focused tests for enrolment, confirmation, login verification, replay, disablement,
   reset, and inactive-account rejection.

## Open Questions

- Should TOTP recovery workflow include a separate admin-only challenge when policy
  requires high-risk reset paths?
