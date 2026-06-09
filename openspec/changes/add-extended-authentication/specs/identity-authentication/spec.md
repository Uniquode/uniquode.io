## MODIFIED Requirements

### Requirement: Canonical local user identity
The system SHALL use a local user account as the canonical identity record for
browser, API, password, and linked external-provider authentication.

#### Scenario: Local account is canonical
- **WHEN** a user authenticates through any supported method
- **THEN** the authenticated subject resolves to a local user account controlled
  by the application

#### Scenario: External identity does not replace local account
- **WHEN** a user authenticates through an external provider
- **THEN** the provider identity is linked to a local account rather than
  becoming the canonical user record

### Requirement: Password-based local sign-in
The system SHALL provide password-based local sign-in for local user accounts
through the FastAPI Users boundary and the shared authentication ceremony.

#### Scenario: Valid credentials create authenticated browser state
- **WHEN** an active local user submits valid password credentials and policy does
  not require a further assertion
- **THEN** the system authenticates the local account and establishes browser
  authentication state

#### Scenario: Valid credentials can require another assertion
- **WHEN** an active local user submits valid password credentials and policy
  requires a further assertion
- **THEN** the system keeps the ceremony incomplete and asks for the next
  permitted assertion instead of issuing browser session state

#### Scenario: Invalid credentials do not authenticate
- **WHEN** a login attempt submits invalid credentials
- **THEN** the system rejects the attempt without authenticating the browser

#### Scenario: Inactive users do not authenticate
- **WHEN** an inactive local user submits valid password credentials
- **THEN** the system rejects the attempt without authenticating the browser

### Requirement: Browser-session authentication
The system SHALL support session-backed browser authentication after a completed
authentication ceremony.

#### Scenario: Authenticated browser request resolves current user
- **WHEN** a browser request includes valid browser session state for an active
  local user
- **THEN** the request can resolve the local user through identity boundaries

#### Scenario: Incomplete ceremony does not resolve session
- **WHEN** a browser request has state for an incomplete ceremony
- **THEN** the request is treated as unauthenticated

#### Scenario: Inactive sessions do not resolve
- **WHEN** session state belongs to an inactive local user
- **THEN** the request is treated as unauthenticated

### Requirement: External-provider ceremony participation
The system SHALL treat linked external-provider assertions as one possible final
ceremony method for local users.

#### Scenario: Linked provider callback satisfies assertion
- **WHEN** an external provider callback is valid for a linked local user
- **THEN** the ceremony records the provider assertion for that local user

#### Scenario: Provider assertion does not bypass local session rules
- **WHEN** policy requires an additional assertion in addition to provider
  callback
- **THEN** the ceremony remains incomplete until all required assertions pass

### Requirement: External identity feature gating
The system SHALL hide optional provider-linking, TOTP, and passkey integration
unless explicitly enabled in wevra authentication configuration.

#### Scenario: Disabled provider linking is not exposed
- **WHEN** provider-linking is disabled in wevra authentication configuration
- **THEN** provider linking routes and login choices are not exposed

#### Scenario: Disabled authentication methods are not exposed
- **WHEN** TOTP or passkey is disabled in wevra authentication configuration
- **THEN** those methods are not offered in the ceremony or login choices

#### Scenario: Inactive local user cannot complete provider assertion
- **WHEN** provider callback resolves to an inactive local user
- **THEN** the ceremony rejects the assertion and does not issue browser
  authentication state
