## ADDED Requirements

### Requirement: GitHub provider enablement
The system SHALL expose GitHub provider login and linking only when GitHub OAuth
is explicitly enabled.

#### Scenario: GitHub provider disabled
- **WHEN** GitHub provider authentication is disabled in host settings
- **THEN** GitHub login and linking routes are not exposed

#### Scenario: GitHub provider requires client configuration
- **WHEN** GitHub is enabled
- **THEN** the system requires GitHub client ID, client secret where
  applicable, callback path, and required scopes

### Requirement: GitHub callback validation
The system SHALL validate GitHub callback state and token responses before any
linking or login assertion is accepted.

#### Scenario: GitHub callback state is enforced
- **WHEN** state is missing, mismatched, expired, or replayed
- **THEN** the system rejects the callback and does not create a session

#### Scenario: GitHub token validation is enforced
- **WHEN** GitHub token response fails validation
- **THEN** the system rejects the callback and returns a branchable auth failure

### Requirement: GitHub subject and claim handling
The system SHALL map GitHub assertions to provider identity records through the
provider-subject link key and any configured claim-mapping rules.

#### Scenario: GitHub subject is the stable provider identifier
- **WHEN** GitHub callback succeeds for a local or linked account
- **THEN** the system uses GitHub `sub` or provider-specific unique identifier
  as the provider subject key for lookup

#### Scenario: GitHub callback resolves linked local account
- **WHEN** GitHub callback maps to an existing provider link
- **THEN** the system resolves the linked local account and records a provider
  assertion for ceremony completion

### Requirement: GitHub account linking lifecycle
The system SHALL support explicit user-initiated linking and unlinking of GitHub
provider identities using shared account-linkage contracts.

#### Scenario: GitHub identity links to authenticated user
- **WHEN** an authenticated user completes GitHub linking flow
- **THEN** the system creates a GitHub provider identity link for that local
  account

#### Scenario: GitHub identity can be unlinked
- **WHEN** GitHub linking is removed for a user
- **THEN** GitHub assertions can no longer resolve that user unless another
  enabled method exists

#### Scenario: GitHub provider metadata is non-authoritative
- **WHEN** a successful GitHub login supplies profile claims
- **THEN** the system stores non-authoritative provider metadata as configured
  and keeps the local user profile canonical
