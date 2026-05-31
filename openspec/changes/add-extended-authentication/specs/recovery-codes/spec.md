## ADDED Requirements

### Requirement: Recovery code set generation
The system SHALL generate high-entropy recovery codes as one-time backup
authenticators for eligible local users.

#### Scenario: User generates recovery codes
- **WHEN** an eligible authenticated user requests recovery codes
- **THEN** the system generates a new set of one-time codes and returns the
  plaintext codes exactly for that generation response

#### Scenario: Recovery codes are stored as verifiers
- **WHEN** recovery codes are persisted
- **THEN** the system stores only verifier values and does not persist plaintext
  recovery codes

#### Scenario: Recovery codes are not redisplayed
- **WHEN** a user later views account security settings
- **THEN** the system does not redisplay existing plaintext recovery codes

### Requirement: Recovery code consumption
The system SHALL allow a valid unused recovery code to satisfy an advanced
authentication ceremony challenge exactly once.

#### Scenario: Valid recovery code completes assertion
- **WHEN** a challenged user submits a valid unused recovery code
- **THEN** the system atomically consumes the code and records a recovery-code
  assertion for the ceremony

#### Scenario: Consumed recovery code cannot be reused
- **WHEN** a consumed recovery code is submitted again
- **THEN** the system rejects it and does not issue browser session state

#### Scenario: Invalid recovery code does not reveal account state
- **WHEN** an invalid recovery code is submitted during a public challenge flow
- **THEN** the system returns the configured neutral challenge failure without
  exposing whether other codes exist

#### Scenario: Inactive user cannot use recovery code
- **WHEN** a user becomes inactive or effectively expired before submitting a
  recovery code
- **THEN** the ceremony rejects the recovery code and does not issue browser
  session state

### Requirement: Recovery code regeneration and revocation
The system SHALL replace or revoke recovery-code sets atomically.

#### Scenario: Regeneration revokes prior codes
- **WHEN** a user regenerates recovery codes
- **THEN** the system atomically revokes all prior unused recovery codes and
  creates a new set

#### Scenario: User revokes recovery codes
- **WHEN** an authenticated user revokes recovery codes
- **THEN** no existing recovery code for that user can satisfy a future
  ceremony challenge

#### Scenario: Administrator resets recovery codes
- **WHEN** an authorised administrator resets recovery codes for a user
- **THEN** the system revokes the existing recovery-code set without exposing
  any plaintext codes

### Requirement: Recovery code status
The system SHALL expose only non-sensitive recovery-code status needed for
account security UX and policy decisions.

#### Scenario: Remaining count is available
- **WHEN** an authenticated user views account security state
- **THEN** the system can report the number of remaining unused recovery codes
  without exposing their values

#### Scenario: Low remaining count can be signalled
- **WHEN** the remaining recovery-code count is below configured policy
- **THEN** the system can surface a non-sensitive warning that regeneration is
  recommended

### Requirement: Recovery code last-method protection
The system SHALL protect users from losing their last usable authentication or
recovery method by default.

#### Scenario: Revocation would remove last method
- **WHEN** revoking recovery codes would leave a user without any permitted
  login or recovery method
- **THEN** the system rejects revocation unless explicit administrative recovery
  policy allows it

#### Scenario: Regeneration preserves recovery path
- **WHEN** recovery-code regeneration succeeds
- **THEN** the user has a new usable recovery-code set before the previous set
  is considered unavailable
