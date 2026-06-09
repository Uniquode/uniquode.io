## Why

Linear: [UT-228](https://linear.app/uniquode/issue/UT-228/add-totp-support)

TOTP remains a concrete advanced-authentication slice requested in `add-extended-authentication`.
It should be planned and implemented independently so we can deliver secret-based second-factor flow without coupling it to every other provider/authentication feature.

## What Changes

- Define a complete TOTP feature contract under `wevra.auth`.
- Require explicit enablement and host policy before exposing setup or challenge flows.
- Define enrolment, confirmation, login participation, secret handling, replay controls,
  disablement, and reset behaviour for TOTP credentials.
- Keep method-specific behaviour decoupled from provider-specific login and passkey work.

## Capabilities

### New Capabilities

- `totp`: concrete TOTP enrolment, confirmation, login participation, and management
  requirements for local accounts.

### Modified Capabilities

- `identity-authentication`: include TOTP as an optional method assertion in the
  authentication ceremony model.
- `fastapi-users-auth-ext`: add TOTP contracts in the ceremony and storage protocol
  layer.

## Impact

- `wevra.auth` and `fastapi-users-auth-ext` receive focused TOTP capability
  requirements.
- Existing password sign-in and session flows should remain unchanged.
- No external OAuth or passkey runtime path is introduced in this change.
