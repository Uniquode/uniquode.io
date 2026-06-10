## Context

The existing authentication ceremony boundary supports primary assertions plus
additional method steps before final browser session issuance.

TOTP should remain within this model as a standalone method that can be enabled,
enrolled, and required by policy.

The policy is tri-state and must be explicit:

- `disabled`: no TOTP setup/challenge route or UI fragment is exposed.
- `opt_in`: TOTP can be set up where eligible and is offered as an optional security enhancement.
- `required`: missing TOTP is surfaced as a prompt after login and after email verification, with a bypass that re-prompts next login.

## Goals / Non-Goals

**Goals:**

- Define TOTP requirements independently from provider and passkey slices.
- Preserve existing ceremony gating (`is_active`, expiry, and required-method policy).
- Keep core login page form stable and render advanced-factor fragments via HTMX.
- Define secret protection so plaintext seeds are never exposed outside enrolment/verification surfaces.
- Store reversible TOTP seed material encrypted at rest and name encrypted fields with a
  `crypt_` prefix.
- Use cryptographically secure random generation for TOTP secrets and recovery codes.

**Non-Goals:**

- Do not implement concrete third-party OAuth or WebAuthn code.
- Do not add runtime dependencies beyond what `add-totp-support` implementation requires.
- Do not redefine provider linking or external account creation policy.

## Decisions

### Login and policy are HTMX-driven

The login form remains a single flow, submitted through HTMX first to determine the
user’s current authentication context before the final challenge submission.

- Default render: email and password only.
- If TOTP is not configured yet and policy requires setup, return a dismissible setup fragment.
- If an active TOTP is available or policy requires active challenge, return a TOTP challenge field and submit path that validates password + optional code in one flow.

### TOTP as a method assertion

TOTP is modelled as a method assertion that can satisfy a configured ceremony policy.
This keeps policy evaluation and session issuance in one place.

### Pending state before active state

TOTP enrolment should create a pending credential, and only a successful confirmation
turns it into an active credential for ceremony assertion.

`opt_in` setup is only permitted for verified email addresses.

### Replay and window as explicit security controls

Time-step windows and replay handling must be configurable by host policy. A narrow
default that favours security is preferred.

### Recovery code fallback

Recovery code bypass is part of the same ceremony surface as TOTP verification.
- Codes are generated at enrolment and stored as single-use alternatives.
- A successful recovery code assertion can complete the ceremony when policy allows it.
- Recovery code use is recorded and the code is consumed atomically.

### Secret handling is sensitive-by-default

The TOTP seed contract should prevent passive disclosure in templates, logs,
and management data structures, while still allowing verification.

TOTP seed persistence must use encrypted-at-rest storage because verification requires
recovering the shared seed. Any field or column containing encrypted secret material
must start with `crypt_` so callers can distinguish encrypted values from plaintext or
one-way verifiers. Persisted plaintext TOTP seed fields are not permitted.

TOTP seed encryption must use the same versioned Wevra secret envelope service and key
ring as other `crypt_` fields. The key-ring configuration should be universal to Wevra
secret storage, not provider-specific; use `WEVRA_SECRET_KEY_CURRENT` for new
encryption and `WEVRA_SECRET_KEY_LEGACY` for comma-separated historical keys. New
values are encrypted with the current key version, and existing values can be decrypted
with current or legacy versions.

Recovery codes are alternate credentials, but the system does not need to recover their
plaintext values after enrolment. They should be stored as one-way secret verifiers,
preferably keyed or peppered with configured secret material rather than plain unsalted
SHA-256. One-way verifier fields must not use the `crypt_` prefix. If a later requirement
introduces reversible encrypted recovery-code storage, those fields must use the `crypt_`
prefix and must not expose decrypted values outside enrolment or verification paths.

## Migration Plan

1. Create focused TOTP requirements (`specs/totp`).
2. Update `identity-authentication` and `fastapi-users-auth-ext` change sets to consume
   TOTP assertions when enabled.
3. Keep provider and passkey implementations untouched by this change.
4. Add focused tests for enrolment, confirmation, login verification, replay, bypass,
   disablement, reset, and inactive-account rejection.
5. Rename existing persisted TOTP seed columns/attributes to `crypt_`-prefixed names
   as part of the migration for encrypted-at-rest storage.
6. Generalise existing secret-key configuration names so all Wevra `crypt_` fields share
   `WEVRA_SECRET_KEY_CURRENT` and `WEVRA_SECRET_KEY_LEGACY`.

## Open Questions

- Should bypass to required mode be explicit by policy (for example temporary bypass window)
  or default to always immediate re-prompt next login?
- Should recovery-code bypass be available for every account in required mode or only under
  explicit admin-enabled account policy?
