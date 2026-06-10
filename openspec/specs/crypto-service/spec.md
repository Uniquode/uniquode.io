# crypto-service Specification

## Purpose
TBD - created by archiving change encrypt-secrets. Update Purpose after archive.
## Requirements
### Requirement: Reversible secrets are encrypted at rest
The system SHALL store reversible secret values in encrypted fields when those
values must be persisted and later recovered as plaintext for an operation.

#### Scenario: Secret fields use crypt prefix
- **WHEN** a persisted field stores a reversible encrypted secret
- **THEN** the field name SHALL start with `crypt_`
- **AND** the field SHALL contain an encrypted secret envelope rather than plaintext.

#### Scenario: Plaintext is decrypted near use
- **WHEN** a caller needs to use a persisted reversible secret
- **THEN** the caller SHALL decrypt the value as close as practical to the use boundary
- **AND** the decrypted value SHALL not be written back to persistence or retained in
  unrelated application state.

#### Scenario: Encrypted values have an explicit value object
- **WHEN** application code passes a persisted reversible encrypted secret across a
  service or persistence boundary
- **THEN** the value SHOULD be represented as a `SecretEnvelope` value object rather
  than a bare plaintext string
- **AND** the value object SHALL carry the encrypted envelope value without loading
  key material itself.

#### Scenario: Crypto service remains the key-aware component
- **WHEN** a `SecretEnvelope` is created from plaintext or decrypted to plaintext
- **THEN** the operation SHALL require an explicit `SecretEnvelopeService`
- **AND** key loading, key selection, rotation, encryption, and decryption SHALL remain
  owned by `SecretEnvelopeService`.

#### Scenario: One-way verifiers are not crypt fields
- **WHEN** a persisted value is a one-way verifier rather than reversible ciphertext
- **THEN** the field SHALL not use the `crypt_` prefix unless reversible encryption is
  also introduced for that value.

### Requirement: Crypto service provides versioned envelope encryption and decryption
The system SHALL provide a shared `wevra.services.crypto` service for encrypting and
decrypting sensitive secret material used by identity integrations.

#### Scenario: Encryption returns a versioned secret envelope
- **WHEN** a caller requests encryption of a secret value
- **THEN** the service SHALL return a non-empty string envelope containing a
  version marker and encrypted payload,
- **AND** the envelope SHALL contain enough information to decode the matching
  decryption method.
- **AND** the envelope SHALL include a key version identifier so decryption can
  select the correct key policy.

#### Scenario: Decrypt returns plaintext and version
- **WHEN** a caller requests decryption of a valid encrypted secret envelope
- **THEN** the service SHALL return both:
  - the decrypted plaintext value, and
  - the envelope version used to produce it.
- **AND** the returned version SHALL be validated against the service key configuration
  before returning plaintext.

#### Scenario: Corrupt envelope fails clearly
- **WHEN** decryption is attempted with a malformed encrypted envelope or an encrypted
  envelope referencing an unknown format
- **THEN** the service SHALL raise a configuration/data error rather than returning
  plaintext.

#### Scenario: Explicit compatibility path may read legacy plaintext
- **WHEN** a caller is executing an approved legacy rollout path for a pre-existing
  plaintext value
- **THEN** the caller MAY treat a value that is not an encrypted envelope as legacy
  plaintext
- **AND** the compatibility path SHALL be explicit at the persistence boundary rather
  than implicit in new secret-writing code.

### Requirement: Key versioning and rotation are explicit
The system SHALL represent key material with a versioned label and support rotating
to a new key without changing call sites.

#### Scenario: Valid key versions are accepted
- **WHEN** the service receives key material with a declared key version
- **THEN** it SHALL register that key version as the active decrypt/encrypt target
  for the matching secret use-case.

#### Scenario: Unknown key versions are rejected for required operations
- **WHEN** an encryption/decryption request references an unknown key version
- **THEN** the service SHALL fail with a clear error.

#### Scenario: Supported legacy key versions are preserved
- **WHEN** rotation is configured with a current key and one or more legacy keys
- **THEN** the service SHALL decrypt values produced with prior versions while only
  encrypting new values with the current key version.

### Requirement: Key material is resolved lazily per use
The system SHALL defer key loading until an encryption or decryption operation is
required and the caller indicates that the operation belongs to a secret use-case.

#### Scenario: No key at startup is tolerated when not used
- **WHEN** the service is created without a key available
- **AND** no caller performs a crypto operation
- **THEN** the application SHALL continue startup without hard failure.

#### Scenario: Key is loaded on first required operation
- **WHEN** an operation requiring secrets is first requested
- **THEN** the service SHALL load and validate key material at that time.

### Requirement: Encryption is enforced only for modules that require it
The system SHALL make it possible for consuming modules to declare whether their
type of operation requires encrypted storage.

#### Scenario: Optional usage does not block startup
- **WHEN** the application enables a feature path that does not require secret
  cryptography
- **THEN** the application SHALL not fail startup or operations on missing secret key
  for that path.

#### Scenario: Required usage fails fast if key is missing or invalid
- **WHEN** a required feature (for example external provider credential storage)
  requests encryption or decryption without a resolvable valid key
- **THEN** the service SHALL fail with a clear validation error before using
default storage semantics.

### Requirement: Provider credentials use encrypted secret fields
The system SHALL persist provider credentials in encrypted `crypt_*` fields and
avoid plaintext provider token storage.

#### Scenario: Provider token save encrypts secrets
- **WHEN** provider credential persistence receives an access token or refresh token
- **THEN** the persistence path SHALL encrypt each supplied token before storage
- **AND** the encrypted values SHALL be stored in `crypt_access_token` and
  `crypt_refresh_token` respectively.

#### Scenario: Provider token load decrypts only at provider use boundary
- **WHEN** an external provider operation requires a persisted token value
- **THEN** the provider path SHALL decrypt the relevant `crypt_*` value close to the
  provider call that requires plaintext
- **AND** intermediate persistence and model paths SHALL continue to carry the
  encrypted value.

#### Scenario: Provider secret operations require configured keys
- **WHEN** a provider credential save or provider-token use operation requires
  encryption or decryption
- **THEN** missing or invalid secret keys SHALL fail the operation clearly.

#### Scenario: Provider-disabled operation does not require keys
- **WHEN** external provider credential operations are disabled or unused
- **THEN** missing secret keys SHALL NOT fail unrelated identity operations.

### Requirement: Key source is external and environment-driven
The system SHALL keep key material out of code and resolve it from environment-backed
configuration.

#### Scenario: Supported key inputs are accepted from environment
- **WHEN** the environment provides supported key settings
- **THEN** the service SHALL load key bytes through the existing env/config pathway
  used by wevra.

#### Scenario: Weak or malformed key material is rejected
- **WHEN** key material is present but not decodable or not valid for the configured
  crypto envelope
- **THEN** the service SHALL reject it with a clear error and refuse to perform
  encrypt/decrypt operations.

#### Scenario: Key material includes a validation checksum
- **WHEN** a configured key is provided
- **THEN** the service SHALL verify a configured checksum suffix (for example CRC32) as
  a typo-safety guard after base64 decoding and before use.
