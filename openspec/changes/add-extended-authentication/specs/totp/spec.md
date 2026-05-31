## ADDED Requirements

### Requirement: TOTP feature enablement
The system SHALL expose TOTP flows only when TOTP is enabled through explicit
identity configuration or host policy.

#### Scenario: TOTP disabled hides setup and login challenge
- **WHEN** TOTP is disabled for the deployment
- **THEN** the system does not expose TOTP enrolment routes, TOTP reset routes,
  or TOTP login challenge choices

#### Scenario: TOTP enabled exposes setup for eligible user
- **WHEN** TOTP is enabled and an eligible authenticated user opens account
  security settings
- **THEN** the system can offer a TOTP enrolment flow for that local user

### Requirement: TOTP enrolment and confirmation
The system SHALL create TOTP credentials through a pending enrolment state that
must be confirmed with a valid TOTP code before the credential becomes active.

#### Scenario: User starts TOTP enrolment
- **WHEN** an eligible authenticated user starts TOTP enrolment
- **THEN** the system creates a pending credential and returns the display data
  needed to configure an authenticator application

#### Scenario: Pending TOTP does not satisfy login policy
- **WHEN** a user has only a pending TOTP credential
- **THEN** that credential does not satisfy any future TOTP login or recovery
  policy until it is confirmed

#### Scenario: User confirms pending TOTP
- **WHEN** the user submits a valid TOTP code for the pending credential
- **THEN** the system activates the credential for future login ceremony checks

#### Scenario: Invalid confirmation keeps credential pending
- **WHEN** the user submits an invalid TOTP code for the pending credential
- **THEN** the system leaves the credential inactive and returns a branchable
  validation failure

### Requirement: TOTP login ceremony verification
The system SHALL allow active TOTP credentials to satisfy a configured login
ceremony challenge.

#### Scenario: Ceremony requests TOTP challenge
- **WHEN** primary authentication succeeds and policy requires TOTP
- **THEN** the ceremony remains incomplete and asks the user for a TOTP code
  instead of issuing final browser session state

#### Scenario: Valid TOTP completes required assertion
- **WHEN** a challenged user submits a valid code for an active TOTP credential
- **THEN** the ceremony records a TOTP assertion and can complete login if all
  policy requirements are satisfied

#### Scenario: Invalid TOTP does not authenticate
- **WHEN** a challenged user submits an invalid TOTP code
- **THEN** the ceremony rejects the assertion without issuing browser session
  state

#### Scenario: Inactive user cannot complete TOTP challenge
- **WHEN** a user becomes inactive or effectively expired before submitting a
  TOTP challenge response
- **THEN** the ceremony rejects the challenge and does not issue browser session
  state

### Requirement: TOTP replay and time-window policy
The system SHALL enforce configured TOTP time-window and replay protections
during confirmation and login verification.

#### Scenario: TOTP outside accepted window fails
- **WHEN** a submitted TOTP code is outside the configured accepted time window
- **THEN** the system rejects the code

#### Scenario: Replayed TOTP code fails
- **WHEN** a submitted TOTP code reuses a time step or verifier already consumed
  for the credential according to replay policy
- **THEN** the system rejects the code

#### Scenario: TOTP policy is configurable
- **WHEN** the deployment configures TOTP step, drift, issuer, or label policy
- **THEN** the system applies those values consistently to enrolment and
  verification

### Requirement: TOTP disablement and reset
The system SHALL support disabling and resetting active TOTP credentials while
preserving account recovery policy.

#### Scenario: User disables TOTP under policy
- **WHEN** an authenticated user satisfies the configured disablement policy
- **THEN** the system disables the active TOTP credential for that user

#### Scenario: Disablement cannot remove last usable method by default
- **WHEN** disabling TOTP would leave the user without any permitted login or
  recovery method
- **THEN** the system rejects disablement unless an explicit administrative
  recovery policy allows it

#### Scenario: TOTP reset invalidates active credential
- **WHEN** a user or authorised administrator resets TOTP for an account
- **THEN** the system invalidates the active TOTP credential and requires a new
  enrolment before TOTP can satisfy login policy again

#### Scenario: Disabled TOTP cannot satisfy challenge
- **WHEN** a disabled or reset TOTP credential is presented during login
- **THEN** the ceremony rejects it as unavailable

### Requirement: TOTP secret protection
The system SHALL protect TOTP seed material from disclosure outside enrolment
and verification flows.

#### Scenario: Plaintext seed is not exposed in records
- **WHEN** TOTP credential records are returned through API, template context,
  logs, or management listings
- **THEN** the plaintext TOTP seed is not included

#### Scenario: Store supports recoverable verification secret
- **WHEN** the system verifies a TOTP code
- **THEN** the credential store provides only the secret access needed for
  verification according to the configured protection mechanism

#### Scenario: Pending enrolment display is limited
- **WHEN** the system returns the enrolment display payload
- **THEN** it does so only during the pending enrolment flow for the eligible
  authenticated user
