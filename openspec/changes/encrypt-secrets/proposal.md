## Why

Linear: [UT-235](https://linear.app/uniquode/issue/UT-235/encrypt-external-identity-provider-secrets)

Sensitive provider secrets used in external authentication (such as `access_token` and
`refresh_token`) are currently stored in plaintext. This is a security risk because
some tokens are long-lived and can be abused if the persistence layer is compromised.

## What Changes

- add application-level encryption for provider credential storage in `wevra.auth`;
- rename persisted credential fields to `crypt_access_token` and
  `crypt_refresh_token` to make encryption-at-rest explicit;
- define migration and runtime handling for encrypted credential fields while preserving
  compatibility with existing tokens during rollout;
- define key versioning and rotation semantics via a cryptographic service so environments can
  safely move between keys without changing encrypted payload schema.

## Capabilities

### New Capabilities

- `identity-secrets-encryption`: encrypted persistence for provider credentials used by
  identity-linked authentication flows.
- `crypto-service`: shared crypto key loading, feature-gated secret requirements,
  key versioning and rotation, and versioned envelope encrypt/decrypt API.

### Modified Capabilities

- `identity-authentication`: credentials are persisted as encrypted `crypt_*` fields, with
  secure load/save contract for provider identity records.

## Impact

- `src/wevra/auth` models and persistence paths handling external provider identities;
- database migrations for encrypted credential columns and compatibility with existing token data.
