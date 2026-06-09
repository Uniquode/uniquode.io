## Context

Passkeys are a distinct second-factor strategy that belongs under the same ceremony model
as other factors but has a dedicated WebAuthn protocol and lifecycle.

## Goals / Non-Goals

**Goals:**

- Define registration, assertion, revocation, and counter policy for passkeys.
- Require valid relying-party configuration before passkey flows are exposed.
- Keep passkey credential persistence in a separate store contract.

**Non-Goals:**

- No OAuth provider logic in this change.
- No TOTP implementation in this change.
- No runtime dependency selection beyond what concrete passkey implementation requires.

## Decisions

### Keep passkey ceremonies explicit

Passkey support should use explicit registration and authentication challenges with
well-defined acceptance and rejection states.

### Library boundary

`wevra.auth` should rely on a concrete passkey library in passkey implementation
rather than duplicating cryptography logic.

### Counter handling as policy

Signature counter policy (including regression handling and zero-count behaviour) is
part of passkey-specific requirements to avoid accidental policy drift.

## Migration Plan

1. Define passkey assertions and store contracts in dedicated `specs/webauthn`.
2. Keep parent ceremony and protocol contracts in existing shared changes.
3. Add passkey-focused tests for registration verification, login assertion, and
   revocation.
