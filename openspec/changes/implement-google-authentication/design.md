## Context

Google OAuth integration should be concrete, explicit, and scoped behind provider
enablement in host settings.

## Goals / Non-Goals

**Goals:**

- Define Google OAuth configuration requirements (`client_id`, secret, callback path,
  scopes, and discovery/issuer trust).
- Define callback validation and claim extraction for Google-specific fields.
- Map Google assertions to shared provider-linked external identity model.

**Non-Goals:**

- Do not redesign account-creation policy; consume the shared policy defined in UT-230.
- Do not implement passkey or TOTP changes in this slice.

## Decisions

### Shared abstraction boundary

Google runtime code should depend on the shared provider-linked identity contracts
defined in UT-173/UT-230 and provide Google-specific inputs only.

### Provider-specific claim mapping

Google claim mapping is explicit and cannot rely on defaults from other providers.

## Migration Plan

1. Add provider-specific Google callback and registration surfaces in Google scope.
2. Add tests for state failure, callback failure, valid login assertion, and linking flow.
3. Keep Google provider changes independent from passkey and other OAuth providers.
