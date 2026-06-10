## Why

Linear: [UT-235](https://linear.app/uniquode/issue/UT-235/encrypt-external-identity-provider-secrets)

Reversible secret values must not be stored in plaintext. Any value that must be
retrieved later, such as provider access tokens, refresh tokens, or MFA seeds, must
be encrypted at rest and decrypted only close to the code path that uses the value.
Field names for reversible encrypted storage must use the `crypt_` prefix so the
encrypted-at-rest contract is visible in the model and schema.

## What Changes

- provide a shared Wevra crypto service for versioned envelope encryption,
  decryption, verifier generation, key validation, and key rotation;
- define a universal current/legacy key contract for all Wevra `crypt_*` fields;
- migrate provider token columns to `crypt_access_token` and `crypt_refresh_token`
  so the schema no longer advertises plaintext token storage;
- complete the remaining provider credential persistence paths so provider secrets
  are encrypted before storage and decrypted only at provider use boundaries;
- document compatibility and failure behaviour for legacy/plaintext rollout values,
  malformed encrypted envelopes, missing keys, and provider-disabled operation.

## Capabilities

### New Capabilities

- `crypto-service`: shared crypto key loading, feature-gated secret requirements,
  key versioning and rotation, versioned envelope encrypt/decrypt API, and
  verifier helpers for one-way secret checks.
- `identity-secrets-encryption`: encrypted persistence contract for reversible
  identity secrets stored in `crypt_*` fields.

### Modified Capabilities

- `identity-authentication`: provider credentials use encrypted `crypt_*` fields
  and must decrypt secrets only at the boundary where the provider operation needs
  the plaintext value.

## Impact

- `src/wevra/services/crypto` key loading, envelope, and verifier service;
- `src/wevra/auth` models and persistence paths handling reversible identity secrets;
- database migrations for encrypted provider credential columns;
- tests and documentation for key configuration, rotation, compatibility, and
  provider-secret operation failure modes.
