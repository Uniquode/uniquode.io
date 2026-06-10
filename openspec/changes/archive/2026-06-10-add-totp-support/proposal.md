## Why

Linear: [UT-228](https://linear.app/uniquode/issue/UT-228/add-totp-support)

TOTP remains a concrete advanced-authentication slice requested in `add-extended-authentication`.
It should be planned and implemented independently so we can deliver secret-based second-factor flow without coupling it to every other authentication feature.

## What Changes

- Define a complete TOTP feature contract under `wevra.auth`.
- Require a tri-state policy (`disabled`, `opt_in`, `required`) and host policy before exposing setup or challenge flows.
- Define enrolment, confirmation, login participation, secret handling, replay controls,
  disablement, and reset behaviour for TOTP credentials.
- Require encrypted-at-rest storage for reversible TOTP secret material, with
  encrypted field names prefixed `crypt_` to make secret-handling expectations explicit.
- Require recovery codes to be stored only as one-way secret verifiers unless a future
  requirement explicitly needs reversible encrypted recovery-code storage.
- Keep method-specific behaviour decoupled from provider-specific login and passkey work.

## Capabilities

### New Capabilities

- `totp`: concrete TOTP enrolment, confirmation, login participation, and management
  requirements for local accounts.

### Modified Capabilities

- `identity-authentication`: include TOTP as an optional or required method assertion in the
  authentication ceremony model.
- `fastapi-users-auth-ext`: add TOTP contracts in the ceremony and storage protocol
  layer.

### Boundary Notes

- `totp_mode = disabled | opt_in | required` is configured in `wevra.auth` and propagated to ceremony policy.
- `disabled`: no TOTP setup/challenge surfaces are exposed.
- `opt_in`: users may enable TOTP after email verification; missing setup does not block login.
- `required`: users with no active TOTP are prompted after primary login and after email verification.
- A user can bypass setup in `required` mode, but will be re-prompted on subsequent logins.
- Login UI and email verification UI transitions are HTMX-driven so fields and challenges can be added/removed without extra JavaScript.
- Enrolment and setup must also return recovery codes where policy permits, used as one-shot bypass options.
- TOTP seed fields that contain encrypted secret material must use a `crypt_` prefix
  (for example `crypt_secret` or `crypt_totp_secret`); plaintext TOTP seeds are not
  valid persisted field values.
- TOTP seed encryption uses the shared Wevra secret envelope/key-ring configuration
  used by other `crypt_` fields, with universal key variables rather than
  provider-specific names.
- Recovery-code persistence must not store raw recovery codes. If the persisted value is
  a one-way verifier, it must not use a `crypt_` prefix; if a reversible encrypted value
  is ever introduced, the field name must use the `crypt_` prefix.

## Impact

- `wevra.auth` and `fastapi-users-auth-ext` receive focused TOTP capability
  requirements.
- Existing password sign-in and session flows remain intact, with ceremony-aware extensions.
- No external OAuth or passkey runtime path is introduced in this change.
