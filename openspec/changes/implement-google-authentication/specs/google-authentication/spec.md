## ADDED Requirements

### Requirement: Google provider enablement
The system SHALL expose Google provider login and linking only when Google OAuth
is explicitly enabled.

#### Scenario: Google provider disabled
- **WHEN** Google provider authentication is disabled in host settings
- **THEN** Google login and linking routes are not exposed

#### Scenario: Google provider requires client configuration
- **WHEN** Google is enabled
- **THEN** the system requires Google OAuth client ID, client secret, callback
  path, required scopes, and trusted issuer configuration

### Requirement: Google callback validation
The system SHALL validate Google callback state and token responses before any
linking or login assertion is accepted.

#### Scenario: Google callback state is enforced
- **WHEN** state is missing, mismatched, expired, or replayed
- **THEN** the system rejects the callback and does not create a session

#### Scenario: Google token validation is enforced
- **WHEN** Google token response or ID token fails validation
- **THEN** the system rejects the callback and records a branchable auth failure

### Requirement: Google subject and claim handling
The system SHALL map Google assertions to provider identity records through the
provider-subject link key and any configured claim-mapping rules.

#### Scenario: Google subject is the stable provider identifier
- **WHEN** Google callback succeeds for a local or linked account
- **THEN** the system uses Google `sub` as the provider subject key for lookup

#### Scenario: Google callback resolves linked local account
- **WHEN** Google callback maps to an existing provider link
- **THEN** the system resolves the linked local account and records a provider
  assertion for ceremony completion

### Requirement: Google account linking lifecycle
The system SHALL support explicit user-initiated linking and unlinking of Google
provider identities using shared account-linkage contracts.

#### Scenario: Google identity links to authenticated user
- **WHEN** an authenticated user completes Google linking flow
- **THEN** the system creates a Google provider identity link for that local
  account

#### Scenario: Google identity can be unlinked
- **WHEN** Google linking is removed for a user
- **THEN** Google assertions can no longer resolve that user unless another
  enabled method exists

#### Scenario: Google provider metadata is non-authoritative
- **WHEN** a successful Google login supplies profile claims
- **THEN** the system stores non-authoritative provider metadata as configured
  and keeps the local user profile canonical
