## MODIFIED Requirements

### Requirement: Canonical local user identity
The system SHALL use a local user account as the canonical identity record for
browser, API, password, TOTP, recovery-code, WebAuthn/passkey, and
third-party-provider authentication.

#### Scenario: Local account is canonical
- **WHEN** a user authenticates through any supported login method
- **THEN** the authenticated subject resolves to a local user account controlled
  by the application

#### Scenario: External identity does not replace local account
- **WHEN** a user authenticates through an external provider
- **THEN** the provider identity is linked to a local account rather than
  becoming the canonical user record

#### Scenario: Advanced authenticator attaches to local account
- **WHEN** a user enrols TOTP, recovery codes, or WebAuthn/passkeys
- **THEN** those authenticators attach to the local account rather than forming
  separate principal records

### Requirement: Password-based local sign-in
The system SHALL provide password-based local sign-in for local user accounts
through the FastAPI Users identity boundary and the shared authentication
ceremony.

#### Scenario: Valid credentials create authenticated browser state
- **WHEN** an active local user submits valid password credentials and no
  additional ceremony requirement applies
- **THEN** the system authenticates the local account and establishes the
  configured browser authentication state

#### Scenario: Valid credentials can require another method
- **WHEN** an active local user submits valid password credentials and policy
  requires TOTP, recovery-code, WebAuthn, provider, or another assertion
- **THEN** the system keeps the ceremony incomplete and asks for a permitted
  next method instead of issuing browser session state

#### Scenario: Invalid credentials do not authenticate
- **WHEN** a login attempt submits invalid credentials
- **THEN** the system rejects the attempt without establishing authenticated
  browser state

#### Scenario: Inactive users do not authenticate
- **WHEN** an inactive local user submits valid password credentials
- **THEN** the system rejects the attempt without establishing authenticated
  browser state

#### Scenario: Login redirects stay same-origin
- **WHEN** a login request includes a return target
- **THEN** the target is accepted only when it is a same-origin relative path
  and unsafe targets fall back to the account page

### Requirement: Browser-session authentication
The system SHALL support session-backed browser authentication as the primary
human-user login mechanism after an authentication ceremony is complete.

#### Scenario: Authenticated browser request resolves current user
- **WHEN** a browser request includes valid authenticated session state for an
  active local user
- **THEN** the request can resolve the current local user through the identity
  boundary

#### Scenario: Inactive sessions do not resolve
- **WHEN** a browser request includes session state for an inactive local user
- **THEN** the request is treated as unauthenticated

#### Scenario: Incomplete ceremony does not resolve session
- **WHEN** a browser request includes state for an incomplete authentication
  ceremony
- **THEN** the request is not treated as an authenticated browser session

#### Scenario: Logout clears browser authentication state
- **WHEN** an authenticated user logs out
- **THEN** the browser authentication state is invalidated or cleared so later
  requests are unauthenticated

### Requirement: Advanced authentication extension points
The system SHALL support concrete TOTP, WebAuthn/passkey, recovery-code, and
linked external-provider authentication capabilities through the reusable
`wevra.auth` boundary without requiring every deployment to enable every method.

#### Scenario: Baseline login can be extended by second factor
- **WHEN** policy requires a second factor for a user
- **THEN** the identity foundation can route successful primary authentication
  into an advanced-authentication challenge before final login completion

#### Scenario: TOTP can satisfy ceremony policy
- **WHEN** TOTP is enabled and the user submits a valid active TOTP code for a
  ceremony challenge
- **THEN** the ceremony can record the TOTP assertion toward final login
  completion

#### Scenario: Recovery code can satisfy ceremony policy
- **WHEN** recovery codes are enabled and the user submits a valid unused
  recovery code for a ceremony challenge
- **THEN** the ceremony can consume the code and record the recovery assertion
  toward final login completion

#### Scenario: WebAuthn can satisfy ceremony policy
- **WHEN** WebAuthn is enabled and the user completes a valid passkey assertion
  for a ceremony challenge
- **THEN** the ceremony can record the WebAuthn assertion toward final login
  completion

#### Scenario: Linked provider can satisfy ceremony policy
- **WHEN** third-party OAuth is enabled and an external provider callback maps
  to a linked local account
- **THEN** the ceremony can record the provider assertion toward final login
  completion

#### Scenario: Linked identity storage is concrete
- **WHEN** OAuth provider login support is implemented
- **THEN** linked provider identities attach to local users without changing the
  canonical user model

### Requirement: Integration feature flag abstraction
The system SHALL gate optional identity integrations and authenticator types
through an explicit settings or feature-flag abstraction before exposing their
routes or flows.

#### Scenario: Disabled integration routes are not exposed
- **WHEN** an optional identity integration such as OAuth account linking, TOTP,
  recovery codes, or WebAuthn is disabled by the feature-flag abstraction
- **THEN** the application does not expose that integration's user-facing routes
  or flows

#### Scenario: Enabled integration routes are exposed intentionally
- **WHEN** an optional identity integration is enabled by the feature-flag
  abstraction and required provider or authenticator configuration is present
- **THEN** the application exposes the corresponding integration routes or flows
  intentionally

#### Scenario: Feature flags do not replace policy checks
- **WHEN** an integration route is enabled through the feature-flag abstraction
- **THEN** account creation, account linking, authenticator enrolment, login
  ceremony, and authorisation policy still apply through the identity and
  authorisation boundaries

#### Scenario: Reusable modules do not depend on application settings
- **WHEN** reusable identity modules need integration availability information
- **THEN** they depend on a protocol, callable, or module-local configuration
  object rather than importing the application's owned settings type

#### Scenario: Application settings adapt into integration options
- **WHEN** `uniquode` application settings contain identity integration flags
- **THEN** the application adapts those settings into a separate integration
  options object before passing them to reusable identity modules
