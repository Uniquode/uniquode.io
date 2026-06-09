## ADDED Requirements

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
- **WHEN** decryption is attempted with a malformed or unknown-envelope-format
  string
- **THEN** the service SHALL raise a configuration/data error rather than returning
  plaintext.

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
