## Why

Linear: [UT-173](https://linear.app/uniquode/issue/UT-173/federation-and-advanced-authentication)

The identity foundation now has stable local users, browser sessions, reusable
`wevra.auth` ownership, and an authentication ceremony boundary. The next step is
to define the concrete extended authentication sub-specs that will turn the
reserved TOTP, recovery-code, WebAuthn/passkey, and external-provider hooks into
real package capabilities.

## What Changes

- Define TOTP requirements for login ceremony participation, enrolment,
  confirmation, disabling, and administrative/user reset.
- Define recovery-code requirements for issuing, storing, rotating, consuming,
  regenerating, and revoking backup codes.
- Define WebAuthn/passkey requirements for registration, credential revocation,
  authentication ceremony participation, and signature-counter handling.
- Define third-party OAuth requirements for provider enablement, login ceremony
  participation, local-account linking, unlinking, and provider identity
  lifecycle across providers such as Google, Apple, GitHub, Facebook, and
  LinkedIn.
- Align all extended authentication capabilities with the canonical local user
  identity model, active-account eligibility checks, and package-owned
  `wevra.auth` storage/service boundaries.
- Keep concrete provider UI, product copy, and deployment policy host-owned
  while `wevra.auth` owns reusable flow contracts, state transitions, route
  surfaces, and storage abstractions.
- Preserve host-controlled feature exposure: each authenticator type must be
  enabled explicitly before routes, setup flows, or login choices are exposed.

## Capabilities

### New Capabilities

- `totp`: TOTP enrolment, confirmation, login verification, disablement, and
  reset behaviour for local users.
- `recovery-codes`: Backup recovery codes for users who need a fallback path
  when an advanced authenticator is unavailable.
- `webauthn`: WebAuthn/passkey registration, revocation, and authentication
  ceremony behaviour.
- `third-party-oauth`: External OAuth provider enablement, login, linking, and
  unlinking for local accounts.

### Modified Capabilities

- `fastapi-users-auth-ext`: Move the addon boundary from reserved advanced
  authentication hooks to concrete package-owned extended authentication
  contracts.
- `identity-authentication`: Extend the canonical local-user login ceremony so
  TOTP, recovery codes, WebAuthn/passkeys, and external OAuth providers can
  participate in account login without replacing the local user identity model.

## Impact

- Affected areas include `wevra.auth` challenge/state protocols, identity
  ceremony services, storage abstractions and future ORM models, package route
  surfaces, identity templates, and host configuration.
- Existing password login, session resolution, reset-password, verification,
  and user-management behaviour must remain compatible.
- New runtime dependencies are not selected in this proposal; concrete
  WebAuthn/OAuth/TOTP library decisions belong in the design artifact and must
  remain requirement-scoped.
