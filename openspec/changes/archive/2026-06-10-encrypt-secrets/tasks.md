## 1. Setup

- [x] 1.1 Add `cryptography` dependency to `wevra/pyproject.toml`.
- [x] 1.2 Add `wevra/services/crypto` package skeleton and public exports.
- [x] 1.3 Define secret-key environment/config contract for current and legacy key versions.

## 2. Crypto Service

- [x] 2.1 Implement lazy key material loader with base64 decoding and checksum validation.
- [x] 2.2 Implement key-version registry with current-key selection and legacy-key fallback.
- [x] 2.3 Implement envelope format with version marker and `encrypt` method returning versioned ciphertext.
- [x] 2.4 Implement `decrypt` method returning `(plaintext, envelope_version)`.
- [x] 2.5 Add explicit errors for missing/invalid keys on required operations.
- [x] 2.6 Add unit tests for happy path, missing key, invalid key, unknown envelope, and rotation decode.
- [x] 2.7 Add a `SecretEnvelope` value object for encrypted envelope values while keeping key-aware operations on `SecretEnvelopeService`.

## 3. Auth Model and Migration

- [x] 3.1 Add Alembic migration to introduce `crypt_access_token` and `crypt_refresh_token`.
- [x] 3.2 Verify model fields expose only `crypt_access_token` and `crypt_refresh_token` for reversible provider token storage.
- [x] 3.3 Update provider credential save paths to encrypt access and refresh tokens before persistence and pass encrypted values as `SecretEnvelope` objects at service boundaries.
- [x] 3.4 Update provider credential use paths to decrypt `crypt_*` `SecretEnvelope` values only close to the provider operation that needs plaintext.
- [x] 3.5 Define and implement the explicit compatibility path for pre-existing plaintext provider token values during rollout.
- [x] 3.6 Add model/persistence tests for encrypted provider-token save, retrieve/use-boundary decrypt, and malformed-envelope failure.

## 4. Integration and Safety

- [x] 4.1 Ensure provider-secret operations fail clearly when required keys are missing or invalid.
- [x] 4.2 Add regression coverage showing provider-disabled identity operation does not require configured secret keys.
- [x] 4.3 Document the `crypt_` field contract for reversible encrypted secrets and the non-`crypt_` treatment of one-way verifiers.
- [x] 4.4 Document key version, legacy-key rotation, malformed-envelope, and compatibility behaviour.
- [x] 4.5 Run focused OpenSpec validation for `encrypt-secrets`.
- [x] 4.6 Run the full Wevra test suite before concluding implementation.
