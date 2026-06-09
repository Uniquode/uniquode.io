## ADDED Requirements

### Requirement: Apple provider enablement
The system SHALL expose Apple provider login and linking only when Apple Sign In
is explicitly enabled.

#### Scenario: Apple provider disabled
- **WHEN** Apple provider authentication is disabled in host settings
- **THEN** Apple login and linking routes are not exposed

#### Scenario: Apple provider requires client configuration
- **WHEN** Apple is enabled
- **THEN** the system requires Apple service ID, team identifier, key ID,
  private key, callback path, and audience/issuer configuration as required by
  Apple policy

### Requirement: Apple callback validation
The system SHALL validate Apple callback state and token responses before any
linking or login assertion is accepted.

#### Scenario: Apple callback state is enforced
- **WHEN** state is missing, mismatched, expired, or replayed
- **THEN** the system rejects the callback and does not create a session

#### Scenario: Apple token validation is enforced
- **WHEN** Apple token response or identity token fails configured Apple
  validation
- **THEN** the system rejects the callback and returns a branchable auth failure

### Requirement: Apple subject and claim handling
The system SHALL map Apple assertions to provider identity records through the
provider-subject link key and provider-specific claim rules.

#### Scenario: Apple subject is the stable provider identifier
- **WHEN** Apple callback succeeds for a local or linked account
- **THEN** the system uses Apple `sub` as the provider subject key for lookup

#### Scenario: Apple callback resolves linked local account
- **WHEN** Apple callback maps to an existing provider link
- **THEN** the system resolves the linked local account and records a provider
  assertion for ceremony completion

### Requirement: Apple account linking lifecycle
The system SHALL support explicit user-initiated linking and unlinking of Apple
provider identities using shared account-linkage contracts.

#### Scenario: Apple identity links to authenticated user
- **WHEN** an authenticated user completes Apple linking flow
- **THEN** the system creates an Apple provider identity link for that local
  account

#### Scenario: Apple identity can be unlinked
- **WHEN** Apple linking is removed for a user
- **THEN** Apple assertions can no longer resolve that user unless another
  enabled method exists

#### Scenario: Apple provider metadata is non-authoritative
- **WHEN** a successful Apple login supplies profile claims
- **THEN** the system stores non-authoritative provider metadata as configured
  and keeps the local user profile canonical
