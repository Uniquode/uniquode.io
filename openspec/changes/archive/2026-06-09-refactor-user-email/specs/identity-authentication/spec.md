## MODIFIED Requirements

### Requirement: Password-based local sign-in
The system SHALL provide password-based local sign-in for local user accounts
through the FastAPI Users boundary and the shared authentication ceremony using
`identity_user_email` for lookup by submitted email.

#### Scenario: Valid credentials create authenticated browser state
- **WHEN** an active local user submits valid password credentials and policy
  does not require a further assertion, using any owned email address
- **THEN** the system authenticates the local account and establishes browser
  authentication state

#### Scenario: Valid credentials can require another assertion
- **WHEN** an active local user submits valid password credentials with an owned
  email address and policy requires a further assertion
- **THEN** the system keeps the ceremony incomplete and asks for the next
  permitted assertion instead of issuing browser session state

#### Scenario: Unknown email does not authenticate
- **WHEN** a login attempt submits an email address not owned by any local user
- **THEN** the system rejects the attempt without authentication or session
  establishment

#### Scenario: Inactive users do not authenticate
- **WHEN** an inactive local user submits valid password credentials and owned
  email
- **THEN** the system rejects the attempt without authenticating the browser

### Requirement: External-provider ceremony participation
The system SHALL treat linked external-provider assertions as one possible final
ceremony method for local users after resolving identity from owned email claims.

#### Scenario: Linked provider callback satisfies assertion
- **WHEN** an external provider callback is valid for an email owned by a linked
  local user
- **THEN** the ceremony records the provider assertion for that local user

#### Scenario: Linked provider assertion cannot change email ownership
- **WHEN** an external provider callback contains a verified email that is owned by a
  different user
- **THEN** the callback does not reassign ownership and returns a deterministic
  conflict outcome

#### Scenario: Provider assertion does not bypass local session rules
- **WHEN** policy requires an additional assertion in addition to provider callback
- **THEN** the ceremony remains incomplete until all required assertions pass
