## Context

`encrypt-secrets` addresses plaintext storage of provider credentials in `wevra` authentication persistence. Provider tokens are currently persisted on `IdentityProvider` as `access_token` and `refresh_token`, which can be long-lived and reusable by attackers if database contents are exposed.

Current boundaries in use:
- `wevra.auth.models.IdentityProvider` holds provider identity records.
- Auth settings and environment handling are already centralised in `wevra` modules.
- No dedicated crypto service module exists yet.

The change is security-sensitive, cross-cutting within auth persistence, and introduces migration and key-management questions, so design approval is required before implementation.

## Goals / Non-Goals

**Goals:**
- Introduce a shared wevra crypto service for encrypting/decrypting sensitive secret material.
- Keep env- and config-driven key loading outside application code, with lazy initialisation.
- Add key-versioned envelopes and support rotation with legacy-key decryption.
- Add checksum validation as a typo-safety check.
- Persist provider tokens as encrypted fields (`crypt_access_token`, `crypt_refresh_token`) while maintaining a migration path for existing rows.
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

## Risks / Trade-offs

- **[Risk] Key exposure by environment file or process dump** → **Mitigation:** emphasise secure key storage patterns (vault/secret manager), keep source-of-truth outside source code, and include operational hardening guidance.
- **[Risk] CRC32 is not security-sensitive** → **Mitigation:** document that it is only typo detection and does not replace proper key secrecy.
- **[Risk] Provider tokens are stored in `identity_provider` rows and must migrate from plaintext** → **Mitigation:** migration adds new encrypted columns and supports reading existing plaintext for read compatibility.
- **[Risk] Lazy key loading can delay failure** → **Mitigation:** surface explicit error on first required operation and include test coverage for missing/invalid key scenarios.
- **[Risk] Envelope format drift between algorithm versions** → **Mitigation:** schema-stable envelope prefix with version mapping and explicit unsupported-format rejection.

## Migration Plan

1. Add `cryptography` dependency to `wevra` and create `wevra/services/crypto`.
2. Define config-driven key material contract (current + legacy versions) and validation/parsing helpers.
3. Implement service API with:
   - lazy key material load,
   - versioned encrypt/decrypt.
4. Rename `IdentityProvider.access_token` to `crypt_access_token` and
   `refresh_token` to `crypt_refresh_token` via migration.
5. Update auth persistence paths that read/write provider tokens to call the crypto service.
6. Add compatibility read/write path for existing plaintext tokens where required by migration order.
7. Add migration tests and integration tests for provider enablement without key, valid and invalid keys, and rotation/decryption of prior versions.
8. Add rollout guidance in release notes/docs: rotate to `current` key by changing `key version` and keeping previous version(s) until old rows have been re-written.

Rollback strategy:
- If implementation issues occur, deploy with current key unchanged and preserve legacy keys list empty or previous set.
- New encrypted writes stop at old key when `current` remains unchanged.
- Feature can be temporarily disabled (provider integration disabled) while keys are corrected.
