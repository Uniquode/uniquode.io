## Context

`encrypt-secrets` addresses plaintext storage of reversible secret values in
`wevra` authentication persistence. Provider tokens were originally represented
as `access_token` and `refresh_token`; persisted reversible secrets must now use
`crypt_*` fields, be encrypted at rest, and be decrypted only close to the code
path that needs plaintext.

Current boundaries in use:
- `wevra.auth.models.IdentityProvider` holds provider identity records.
- Auth settings and environment handling are already centralised in `wevra` modules.
- `wevra.services.crypto.SecretEnvelopeService` now provides key loading,
  versioned envelopes, verifier helpers, and key rotation support.

The change is security-sensitive, cross-cutting within auth persistence, and introduces migration and key-management questions, so design approval is required before implementation.

## Goals / Non-Goals

**Goals:**
- Introduce a shared wevra crypto service for encrypting/decrypting sensitive secret material.
- Keep env- and config-driven key loading outside application code, with lazy initialisation.
- Ensure deployments that need encrypted-provider operations fail clearly when a
  provider-secret operation is attempted without valid key material.
- Add key-versioned envelopes and support rotation with legacy-key decryption.
- Add checksum validation as a typo-safety check.
- Persist provider tokens as encrypted fields (`crypt_access_token`,
  `crypt_refresh_token`) while maintaining an explicit compatibility path for
  existing plaintext rows during rollout.
- Represent encrypted reversible secrets crossing service/persistence boundaries
  as `SecretEnvelope` value objects while keeping key-aware work in
  `SecretEnvelopeService`.
- Define clear failure behaviour when encryption is required but keys are unavailable or invalid.

**Non-Goals:**
- Changing auth policy, external provider protocols, or database migration framework.
- Replacing existing session-token handling outside provider token persistence.
- Providing a UI or admin tooling for key rotation workflows.

## Decisions

1. **Create a dedicated service package**

Decision: Add a `wevra.services.crypto` module for encryption/decryption and key-material handling.

Why: This keeps crypto concerns out of feature modules while giving identity, and any future module, a single API and policy model.

Alternatives:
- Keep crypto helpers in `wevra.auth`.
- Keep in host app code.

Rationale: `wevra` owns auth persistence and shared config handling; the service should remain reusable and framework-level.

2. **Use `cryptography` and a versioned envelope format**

Decision: Use `cryptography` for symmetric encryption and always produce envelopes that include:
- crypto format/algorithm marker,
- key version,
- encrypted payload.

Why: `cryptography` is the established standard in this codebase; versioned envelopes preserve readability for decryption routing.

Alternatives:
- Roll custom encryption helpers without envelope metadata.
- Store version only in separate metadata columns.

Rationale: Envelope metadata in the value itself keeps compatibility with existing rows and avoids additional schema surface.

3. **Model encryption requirements as secret-use opt-in and explicit**

Decision: Consumers must indicate whether an operation requires encrypted secret handling before invoking service methods.

Why: This avoids hard failure at import/startup for deployments that do not use provider credential persistence.

Alternatives:
- Fail at startup whenever key is missing.
- Skip all startup checks and fail unpredictably later.

Rationale: lazy initialisation with explicit usage aligns with your requirement: strict only when needed.

Operational rule:
- Provider-secret save/decrypt operations use required crypto operations and
  fail clearly when key material is missing, unparsable, invalid, or lacks the
  referenced key version.
- Deployments that do not use provider-secret operations are not blocked by
  missing secret keys.

4. **Adopt current/legacy key registry pattern**

Decision: Key input resolves to:
- `current` key for encryption and envelope generation,
- zero or more `legacy` keys for decryption fallback.

Why: This supports zero-downtime key rollover.

Alternatives:
- Single-key only, requiring freeze-and-migrate.
- Immediate dual-write re-encryption jobs only.

Rationale: Current/legacy registry preserves service continuity during rotation with minimal operational complexity.

5. **Checksum validation as typo-safety, not cryptographic integrity**

Decision: Validate optional/mandated checksum suffix (for example CRC32) after base64 decode.

Why: It catches key-entry mistakes quickly without adding expensive external infra.

Alternatives:
- No checksum.
- HMAC/signature-based integrity checks on key material.

Rationale: CRC32 is practical and low-cost, with clear security caveat communicated in design.

6. **Use an explicit encrypted value object**

Decision: Add `SecretEnvelope` as the value object for encrypted reversible
secret envelopes passed across service and persistence boundaries.

Why: This makes the encrypted-at-rest contract visible in types and reduces the
chance of confusing plaintext strings with encrypted `crypt_*` values.

Alternatives:
- Continue passing raw encrypted strings across every boundary.
- Let the value object load keys or decrypt implicitly.

Rationale: `SecretEnvelope` carries encrypted data only. `SecretEnvelopeService`
remains the explicit key-aware component for creation from plaintext and
decryption to plaintext.

## Risks / Trade-offs

- **[Risk] Key exposure by environment file or process dump** → **Mitigation:** emphasise secure key storage patterns (vault/secret manager), keep source-of-truth outside source code, and include operational hardening guidance.
- **[Risk] CRC32 is not security-sensitive** → **Mitigation:** document that it is only typo detection and does not replace proper key secrecy.
- **[Risk] Provider tokens are stored in `identity_provider` rows and must migrate from plaintext** → **Mitigation:** migration adds new encrypted columns and supports reading existing plaintext for read compatibility.
- **[Risk] Lazy key loading can delay failure** → **Mitigation:** surface explicit error on first required provider-secret operation and include test coverage for missing/invalid key scenarios.
- **[Risk] Envelope format drift between algorithm versions** → **Mitigation:** schema-stable envelope prefix with version mapping and explicit unsupported-format rejection.

## Migration Plan

1. Add `cryptography` dependency to `wevra` and create `wevra/services/crypto`.
2. Define config-driven key material contract (current + legacy versions) and validation/parsing helpers.
3. Implement service API with:
   - lazy key material load,
   - versioned encrypt/decrypt,
   - required-operation failure for missing or invalid key material,
   - one-way verifier helpers for non-reversible secret checks.
4. Add `SecretEnvelope` as the encrypted value object for reversible persisted
   secrets.
5. Rename `IdentityProvider.access_token` to `crypt_access_token` and
   `refresh_token` to `crypt_refresh_token` via migration.
6. Add a provider credential persistence boundary that encrypts token values on
   save and exposes encrypted values as `SecretEnvelope` objects.
7. Add explicit decrypt methods for provider-token use boundaries.
8. Add compatibility handling for existing plaintext tokens where required by
   migration order, while rejecting malformed encrypted-looking envelopes.
9. Add migration/service tests and integration tests for provider-secret
   operations without keys, provider-disabled configuration without keys,
   valid keys, invalid envelopes, and rotation/decryption of prior versions.
10. Add rollout guidance in release notes/docs: rotate to `current` key by
    changing `key version` and keeping previous version(s) in the legacy list
    until old rows have been rewritten or intentionally invalidated.

Rollback strategy:
- If implementation issues occur, deploy with current key unchanged and preserve legacy keys list empty or previous set.
- New encrypted writes stop at old key when `current` remains unchanged.
- Provider-secret operations can be temporarily disabled or avoided while keys
  are corrected; unrelated identity operations should continue without requiring
  secret key configuration.
