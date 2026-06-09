## Why

Linear: [UT-234](https://linear.app/uniquode/issue/UT-234/refactor-user-email)

Local users currently rely on a single email on the `identity_user` row, which prevents correct support for users owning multiple email addresses and introduces ambiguity at authentication boundaries. This change is required to support a clean, future-facing identity model now, since there is no existing production data and no backward compatibility constraint.

## What Changes

- Create a dedicated `identity_user_email` table to model ownership of zero-or-more user email addresses with global uniqueness per email.
- Enforce a one-to-one rule that an email address can be associated with exactly one local user.
- Update password sign-in lookup so any verified/owned email can be used to start a login ceremony.
- Update password + TOTP sign-in so ceremony user resolution happens against the email table before any authenticator checks.
- Update external provider callback login/linking so provider email claims resolve through the same email ownership model.
- Ensure passkey identity is bound to the local user and can coexist with multiple email addresses.
- Introduce migration and domain constraints to guarantee deterministic uniqueness and prevent cross-account email collisions.
- Keep `identity_user` model and host-level account bootstrapping semantics intact, while moving email ownership into a separate relation.

## Capabilities

### New Capabilities

- `user-email-identity`: one-to-many user-to-email ownership with global email uniqueness and canonical primary-email selection.
- `email-identity-authentication-lookup`: authentication user resolution by any owned email for password and challenge-based flows.

### Modified Capabilities

- `identity-authentication`: replace direct `identity_user.email` lookup for login/start-of-ceremony resolution with canonical email relation resolution.
- `fastapi-users-auth-ext`: keep challenge and authenticator flow contracts unchanged, but resolve login principals through the new email relation.

## Impact

- New model and migration work in `wevra.auth`: `identity_user_email`, unique constraints/indexes, and model metadata.
- Update authentication flow in `wevra.auth` to resolve credentials and provider callbacks by email ownership, including password and MFA-enabled flows.
- Update tests in `wevra` and `app` around login and identity resolution to assert multiple email ownership and uniqueness guarantees.
