## 1. Setup

- [ ] 1.1 Add `cryptography` dependency to `wevra/pyproject.toml`.
- [ ] 1.2 Add `wevra/services/crypto` package skeleton and public exports.
- [ ] 1.3 Define secret-key environment/config contract for current and legacy key versions.

## 2. Crypto Service

- [ ] 2.1 Implement lazy key material loader with base64 decoding and checksum validation.
- [ ] 2.2 Implement key-version registry with current-key selection and legacy-key fallback.
- [ ] 2.3 Implement envelope format with version marker and `encrypt` method returning versioned ciphertext.
- [ ] 2.4 Implement `decrypt` method returning `(plaintext, envelope_version)`.
- [ ] 2.5 Add explicit errors for missing/invalid keys on required operations.
- [ ] 2.6 Add unit tests for happy path, missing key, invalid key, unknown envelope, and rotation decode.

## 3. Auth Model and Migration

- [ ] 3.1 Add Alembic migration to introduce `crypt_access_token` and `crypt_refresh_token`.
- [ ] 3.2 Update model fields and persistence paths to use encrypted values.
- [ ] 3.3 Add compatibility read path for existing plaintext token values during rollout.
- [ ] 3.4 Add model/persistence tests for encrypted provider-token save and retrieve.

## 4. Integration and Safety

- [ ] 4.1 Integrate crypto service into provider persistence flow and mark secret-using operations explicitly.
- [ ] 4.2 Ensure missing/invalid keys only fail when provider-secret operations are required.
- [ ] 4.3 Add regression test for feature-gated usage without keys when providers are disabled.
- [ ] 4.4 Update docs/spec notes to include key version/rotation behaviour and operational guidance.
