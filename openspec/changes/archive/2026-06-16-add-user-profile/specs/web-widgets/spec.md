## ADDED Requirements

### Requirement: Login widget consumes profile image descriptors
The system SHALL have the login widget consume profile-owned image descriptors when rendering authenticated user avatar data.

#### Scenario: Profile capability provides avatar data
- **WHEN** the login widget renders an authenticated user
- **AND** the profile capability is available
- **THEN** the widget obtains profile image display data from profile
- **AND** renders the returned image source or fallback text

#### Scenario: Profile capability is unavailable
- **WHEN** the login widget renders an authenticated user
- **AND** the profile capability is not available
- **THEN** the widget does not depend on auth-owned profile image helpers
- **AND** it renders only behaviour that can be provided without profile data
