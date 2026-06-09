## ADDED Requirements

### Requirement: WebAuthn feature and relying-party configuration
The system SHALL expose WebAuthn/passkey flows only when WebAuthn is enabled
with valid relying-party and origin configuration.

#### Scenario: WebAuthn disabled hides passkey flows
- **WHEN** WebAuthn is disabled for the deployment
- **THEN** the system does not expose passkey registration, revocation, or login
  challenge choices

#### Scenario: WebAuthn requires relying-party configuration
- **WHEN** WebAuthn is enabled
- **THEN** the system requires relying-party ID, relying-party name, allowed
  origins, timeout, and user-verification policy before exposing WebAuthn flows

#### Scenario: Misconfigured WebAuthn fails startup or validation
- **WHEN** required WebAuthn relying-party configuration is missing or invalid
- **THEN** startup or validation fails before WebAuthn routes are exposed

### Requirement: WebAuthn credential registration
The system SHALL register WebAuthn credentials only after a valid browser
registration ceremony succeeds.

#### Scenario: User starts passkey registration
- **WHEN** an eligible authenticated user starts passkey registration
- **THEN** the system creates a registration challenge using the configured
  relying-party policy

#### Scenario: Registration challenge response is verified
- **WHEN** the browser returns a WebAuthn registration response
- **THEN** the system verifies challenge, origin, relying-party ID, user handle,
  attestation policy, and credential public key data before storing a credential

#### Scenario: Valid registration stores credential
- **WHEN** the registration response is valid
- **THEN** the system stores the credential ID, public key, sign count, user
  association, and non-sensitive device metadata

#### Scenario: Invalid registration stores nothing
- **WHEN** the registration response is invalid or expired
- **THEN** the system does not store a WebAuthn credential

### Requirement: WebAuthn login ceremony
The system SHALL allow registered WebAuthn credentials to participate in the
authentication ceremony.

#### Scenario: User starts passkey login
- **WHEN** WebAuthn login is available for the requested account or login
  context
- **THEN** the system creates an authentication challenge for the allowed
  credentials or discoverable credential policy

#### Scenario: Valid passkey assertion completes assertion
- **WHEN** the browser returns a valid WebAuthn authentication assertion
- **THEN** the system records a WebAuthn assertion for the ceremony and can
  complete login if all policy requirements are satisfied

#### Scenario: Invalid passkey assertion does not authenticate
- **WHEN** the browser returns an invalid or expired WebAuthn assertion
- **THEN** the system rejects the assertion without issuing browser session
  state

#### Scenario: Inactive user cannot complete WebAuthn login
- **WHEN** a user becomes inactive or effectively expired before completing a
  WebAuthn challenge
- **THEN** the ceremony rejects the challenge and does not issue browser session
  state

### Requirement: WebAuthn credential revocation
The system SHALL support revoking individual WebAuthn credentials.

#### Scenario: User revokes own passkey
- **WHEN** an authenticated user revokes one of their WebAuthn credentials
- **THEN** the credential can no longer satisfy login ceremony policy

#### Scenario: Administrator revokes passkey
- **WHEN** an authorised administrator revokes a WebAuthn credential for a user
- **THEN** the credential can no longer satisfy login ceremony policy

#### Scenario: Revocation cannot remove last usable method by default
- **WHEN** revoking a WebAuthn credential would leave a user without any
  permitted login or recovery method
- **THEN** the system rejects revocation unless explicit administrative recovery
  policy allows it

### Requirement: WebAuthn signature counter and clone protection
The system SHALL update WebAuthn credential sign counters and expose branchable
failure results for suspicious counter behaviour.

#### Scenario: Successful assertion updates sign count
- **WHEN** a WebAuthn authentication assertion is accepted with a newer sign
  count
- **THEN** the system persists the updated sign count for that credential

#### Scenario: Counter regression fails authentication
- **WHEN** a WebAuthn assertion presents a sign count that violates clone
  detection policy
- **THEN** the system rejects the assertion and returns a branchable credential
  risk result

#### Scenario: Zero counter policy is explicit
- **WHEN** a credential or authenticator uses a zero or non-incrementing sign
  count
- **THEN** the system handles it according to explicit configured WebAuthn
  counter policy
