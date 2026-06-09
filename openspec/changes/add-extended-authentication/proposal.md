## Why

Linear: [UT-173](https://linear.app/uniquode/issue/UT-173/federation-and-advanced-authentication)

The identity foundation has stable local users, browser sessions, reusable
`wevra.auth` ownership, and an authentication ceremony boundary. The next step
is to define the external identity model and account-linkage flows that all
provider-specific implementations can consume.

## What Changes

- Define an external provider identity model and canonical local-account linkage.
- Define provider link and unlink flows, including lifecycle, stale-link
  protections, and host-visible account usability constraints.
- Define provider callback and challenge contracts in `wevra.auth` so provider
  implementations can share a common account-resolution and assertion model.
- Define normalised provider identity persistence in `wevra` and feature gates for
  optional provider, TOTP, and passkey flows.
- Keep concrete provider implementations, detailed provider-specific policy
  decisions in separate issues.

## Capabilities

### New Capabilities

- `external-identity`: external provider identity records and local-account link
  records.
- `authentication-method-flags`: shared wevra flags governing optional provider,
  TOTP, and passkey capabilities.

### Modified Capabilities

- `fastapi-users-auth-ext`: own provider identity and account-linkage contracts in
  shared package protocols.
- `identity-authentication`: include external provider assertions in the shared
  authentication ceremony without replacing the local user identity model.

## Impact

- Affected areas include `wevra.auth` challenge/state protocols, identity
  ceremony services, storage abstractions, and ORM models.
- Existing password login, session resolution, reset-password, verification, and
  user-management behaviour remains unchanged unless feature flags enable
  additional providers.
- New provider, TOTP, passkey, and policy-specific runtime decisions remain in
  follow-on slices.
