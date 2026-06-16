## Why

Linear: [UT-229](https://linear.app/uniquode/issue/UT-229/add-passkey-support)

Passkeys are now a separate advanced-authentication slice and should be defined as an
independent implementation plan instead of being bundled with every other authentication path.

## What Changes

- Define WebAuthn/passkey registration, authentication, and credential revocation
  requirements in `wybra.auth`.
- Define relying-party configuration and challenge lifecycles as passkey-specific concerns.
- Keep provider and TOTP slices independent from passkey requirement planning.

## Capabilities

### New Capabilities

- `webauthn`: concrete passkey registration, authentication, and revocation requirements.

### Modified Capabilities

- `identity-authentication`: include passkey assertions in the shared ceremony model.
- `fastapi-users-auth-ext`: add passkey assertion, challenge, and credential state contracts.

## Impact

- Introduces a dedicated passkey slice that can be implemented and validated independently.
- No Google/GitHub/Apple provider work is included here.
