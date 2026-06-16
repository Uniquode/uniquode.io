## ADDED Requirements

### Requirement: Auth does not own profile presentation
The system SHALL keep reusable auth responsible for identity and current-user resolution rather than profile image presentation.

#### Scenario: Current user is resolved for profile consumers
- **WHEN** profile or widgets need the authenticated user
- **THEN** auth provides identity/current-user data through auth-owned APIs or capabilities
- **AND** profile owns profile display metadata derived from that user

#### Scenario: Profile image helper moves out of auth
- **WHEN** profile image display data is needed
- **THEN** callers use the profile capability
- **AND** auth does not provide the long-term profile image descriptor helper
