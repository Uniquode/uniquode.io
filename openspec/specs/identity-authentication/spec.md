# identity-authentication Specification

## Purpose
Define local user identity, FastAPI Users integration, browser sessions,
account lifecycle hooks, bootstrap behaviour, and identity extension policy.
## Requirements
### Requirement: Canonical local user identity
The system SHALL use a local user account as the canonical identity record for browser, API, and future external-provider authentication.

#### Scenario: Local account is canonical
- **WHEN** a user authenticates through any supported login method
- **THEN** the authenticated subject resolves to a local user account controlled by the application

#### Scenario: External identity does not replace local account
- **WHEN** a user later authenticates through an external provider
- **THEN** the provider identity is linked to a local account rather than becoming the canonical user record

### Requirement: FastAPI Users baseline integration
The system SHALL use FastAPI Users for the baseline local account lifecycle and authentication primitives where they fit the project identity model.

#### Scenario: FastAPI Users dependency is present
- **WHEN** a developer inspects project runtime dependencies
- **THEN** FastAPI Users is included as a runtime dependency for identity foundation work

#### Scenario: Application owns policy around library flows
- **WHEN** FastAPI Users or `wevra.auth` provides account lifecycle or
  authentication primitives
- **THEN** application code still owns account creation policy, email delivery,
  redirects, layout, theme, product navigation, and project-specific error
  handling around those flows

#### Scenario: Auth extension owns reusable identity presentation defaults
- **WHEN** local account lifecycle or authentication primitives need browser
  pages such as login, signup, verification, password reset, account, logout,
  or password change
- **THEN** `wevra.auth` owns the reusable route surfaces and default
  `templates/identity` content for those pages

#### Scenario: Auth extension owns identity data revisions
- **WHEN** local identity tables need Alembic migration revisions
- **THEN** `wevra.auth` owns those revision files alongside its identity models
  and the host migration command includes them only when `wevra.auth` is
  configured

### Requirement: Baseline authentication ceremony
The system SHALL model login as an authentication ceremony that can include
passwords, passkeys, MFA codes, recovery codes, or later provider callbacks
before final browser authentication state is established.

#### Scenario: Login surface supports multiple authenticators
- **WHEN** a user reaches the login surface
- **THEN** the system can offer available authenticators such as password
  sign-in and future passkey challenges without requiring separate login
  surfaces

#### Scenario: Session is issued only after ceremony completion
- **WHEN** an authentication ceremony has intermediate successful steps but
  still requires another authenticator
- **THEN** the system does not establish final browser authentication state
  until the configured ceremony requirements are satisfied

#### Scenario: Inactive accounts cannot complete a ceremony
- **WHEN** any authentication ceremony step resolves to an inactive local user
- **THEN** the system rejects or neutralises the step before final browser
  authentication state can be established

#### Scenario: Finalisation rechecks account eligibility
- **WHEN** the system is about to issue final browser authentication state
- **THEN** it rechecks that the local user is active and eligible rather than
  trusting an earlier ceremony step

### Requirement: Password-based local sign-in
The system SHALL provide password-based local sign-in for local user accounts as
one possible step in the authentication ceremony through the FastAPI Users
identity boundary.

#### Scenario: Valid credentials create authenticated browser state
- **WHEN** an active local user submits valid password credentials and no
  additional authenticator is required
- **THEN** the system authenticates the local account and establishes the configured browser authentication state

#### Scenario: Valid credentials can continue the ceremony
- **WHEN** an active local user submits valid password credentials and policy
  requires another authenticator
- **THEN** the system keeps the authentication ceremony incomplete and requests
  the next required authenticator instead of issuing final browser
  authentication state

#### Scenario: Invalid credentials do not authenticate
- **WHEN** a login attempt submits invalid credentials
- **THEN** the system rejects the attempt without establishing authenticated browser state

#### Scenario: Inactive users do not authenticate
- **WHEN** an inactive local user submits valid password credentials
- **THEN** the system rejects the attempt without establishing authenticated
  browser state

#### Scenario: Blank passwords are not accepted
- **WHEN** a password-based account creation or reset flow receives an empty or
  whitespace-only password
- **THEN** the identity boundary rejects the password without storing usable
  password credentials

#### Scenario: Login redirects stay same-origin
- **WHEN** a login request includes a return target
- **THEN** the target is accepted only when it is a same-origin relative path
  and unsafe targets fall back to the account page

### Requirement: Browser-session authentication
The system SHALL support session-backed browser authentication as the primary human-user login mechanism.

#### Scenario: Authenticated browser request resolves current user
- **WHEN** a browser request includes valid authenticated session state for an
  active local user
- **THEN** the request can resolve the current local user through the identity boundary

#### Scenario: Inactive sessions do not resolve
- **WHEN** a browser request includes session state for an inactive local user
- **THEN** the request is treated as unauthenticated

#### Scenario: Logout clears browser authentication state
- **WHEN** an authenticated user logs out
- **THEN** the browser authentication state is invalidated or cleared so later requests are unauthenticated

### Requirement: Account lifecycle email hooks
The system SHALL provide password reset and email verification flows with application-owned email delivery.

#### Scenario: Password reset request creates delivery hook
- **WHEN** a user requests a password reset for an eligible account
- **THEN** the system creates the reset flow state and invokes an application-owned delivery hook

#### Scenario: Verification request creates delivery hook
- **WHEN** a user requests email verification for an eligible account
- **THEN** the system creates the verification flow state and invokes an application-owned delivery hook

#### Scenario: Public token requests use neutral responses
- **WHEN** a password reset or verification request targets an unknown,
  inactive, or otherwise ineligible account state
- **THEN** the system returns the same neutral public response without exposing
  account state through status codes

#### Scenario: Inactive accounts cannot complete token flows
- **WHEN** a password reset or verification confirmation token resolves to an
  inactive local user
- **THEN** the system rejects the confirmation without activating,
  authenticating, or otherwise making the account eligible

#### Scenario: Public token confirmations preserve internal failure reasons
- **WHEN** a password reset or verification confirmation fails
- **THEN** the identity boundary can expose branchable internal failure reasons
  while public routes still return neutral user-facing responses

#### Scenario: Library does not own email delivery
- **WHEN** email-related account flows are implemented
- **THEN** the application provides sender configuration, message templates, delivery integration, and throttling policy

### Requirement: Optional public signup
The system SHALL keep public self-registration disabled by default while
allowing the host application to enable a public signup flow through explicit
identity policy.

#### Scenario: Public signup disabled by default
- **WHEN** the application uses the default account creation policy
- **THEN** public signup routes or flows are not exposed

#### Scenario: Public signup enabled intentionally
- **WHEN** the account creation policy explicitly allows public signup
- **THEN** the application can expose a host-owned signup route that creates a
  local account through the identity boundary

#### Scenario: Signup follows account eligibility policy
- **WHEN** a public signup flow creates a local account
- **THEN** account activation, verification, and session issuance follow the
  configured identity policy rather than implicitly authenticating every newly
  created account

### Requirement: Identity token signing secrets
The system SHALL require deployment-specific reset-password and verification token signing secrets outside local development.

#### Scenario: Local development can generate secrets
- **WHEN** the application is configured for local development without explicit
  identity token secrets
- **THEN** local-only token secrets are generated rather than using committed
  fixed signing strings

#### Scenario: Non-local deployments require configured secrets
- **WHEN** the application is configured for a non-local deployment
- **THEN** reset-password and verification token signing secrets must be
  explicitly configured before the application starts

#### Scenario: Blank identity token secrets are rejected
- **WHEN** identity token signing secrets are supplied as empty or whitespace
  values
- **THEN** configuration fails rather than treating the values as usable signing
  secrets

### Requirement: Initial administrative bootstrap
The system SHALL define a bootstrap mechanism for creating the initial administrative local user.

#### Scenario: No administrative user exists
- **WHEN** the application is initialised and no administrative local user exists
- **THEN** the bootstrap mechanism can create the initial administrative account through a controlled path

#### Scenario: Administrative user already exists
- **WHEN** at least one administrative local user already exists
- **THEN** the bootstrap mechanism does not silently create additional administrative users

#### Scenario: Concurrent bootstrap attempts
- **WHEN** multiple processes or tasks attempt initial administrative bootstrap at the same time
- **THEN** a database-enforced single-writer mechanism allows only one attempt to create the initial administrative account

### Requirement: Advanced authentication extension points
The system SHALL reserve explicit extension points for TOTP, WebAuthn/passkeys, recovery codes, and linked external identities without requiring those features in the first local-user implementation.

#### Scenario: Baseline ceremony can require additional authenticators
- **WHEN** future policy requires TOTP, WebAuthn/passkey, recovery-code, or
  another authenticator for a user
- **THEN** the identity foundation can keep the authentication ceremony open
  until the required authenticator is satisfied

#### Scenario: Passkey can participate at login
- **WHEN** future passkey support is enabled for a user
- **THEN** the login surface can offer a passkey challenge as part of the
  authentication ceremony before or instead of password entry where policy
  allows

#### Scenario: Linked identity storage is planned
- **WHEN** future OAuth provider login support is implemented
- **THEN** linked provider identities can attach to local users without changing the canonical user model

### Requirement: Integration feature flag abstraction
The system SHALL gate optional identity integrations through an explicit settings or feature-flag abstraction before exposing their routes or flows.

#### Scenario: Disabled integration routes are not exposed
- **WHEN** an optional identity integration such as OAuth account linking is disabled by the feature-flag abstraction
- **THEN** the application does not expose that integration's user-facing routes or flows

#### Scenario: Enabled integration routes are exposed intentionally
- **WHEN** an optional identity integration is enabled by the feature-flag abstraction and required provider configuration is present
- **THEN** the application exposes the corresponding integration routes or flows intentionally

#### Scenario: Feature flags do not replace policy checks
- **WHEN** an integration route is enabled through the feature-flag abstraction
- **THEN** account creation, account linking, and authorisation policy still apply through the identity and authorisation boundaries

#### Scenario: Reusable modules do not depend on application settings
- **WHEN** reusable identity modules need integration availability information
- **THEN** they depend on a protocol, callable, or module-local configuration object rather than importing the application's owned settings type

#### Scenario: Application settings adapt into integration options
- **WHEN** `uniquode` application settings contain identity integration flags
- **THEN** the application adapts those settings into a separate integration options object before passing them to reusable identity modules

### Requirement: Internal OAuth2 provider is deferred
The system SHALL NOT require an internal OAuth2 authorisation provider to support baseline local users and browser login.

#### Scenario: Local user login does not depend on local OAuth2 provider
- **WHEN** password-based browser login is implemented
- **THEN** it operates through the local identity and session boundary without requiring an internal OAuth2 authorisation server

#### Scenario: OAuth2 provider waits for a concrete requirement
- **WHEN** the project designs internal OAuth2 scopes or grants
- **THEN** that work depends on a concrete API, federation, or delegated-access
  requirement and stable local users plus authorisation scopes

#### Scenario: OAuth2 provider is a separate boundary
- **WHEN** internal OAuth2 provider work begins
- **THEN** it is implemented through a separate provider boundary rather than as
  part of baseline local-user authentication

### Requirement: Group-backed capability resolution
The identity boundary SHALL expose local user capabilities through group-backed
effective-scope resolution.

#### Scenario: Authenticated user has group scopes
- **WHEN** an authenticated local user belongs to one or more authorisation
  groups
- **THEN** identity capability resolution exposes the de-duplicated scopes from
  the user's direct and nested group memberships

#### Scenario: No direct user flags are required
- **WHEN** identity capability resolution evaluates a local user
- **THEN** it does not require direct user flags or direct user scope
  assignments

#### Scenario: Existing user booleans remain identity metadata
- **WHEN** identity capability resolution evaluates `is_admin` or
  `is_superuser`
- **THEN** those fields remain existing identity and bootstrap metadata rather
  than the general authorisation scope model

#### Scenario: Capability cache is invalidated by group changes
- **WHEN** group, scope, or membership state changes for a user
- **THEN** later identity capability resolution uses rebuilt effective scopes
  rather than stale cached scopes

### Requirement: Authorisation policy depends on group scopes
The identity boundary SHALL provide group-backed scopes to route, page, partial,
API, and token policy layers that need authorisation decisions.

#### Scenario: Policy requests user scopes
- **WHEN** a route, page, partial, API, or token policy needs a local user's
  scopes
- **THEN** it obtains scopes through the identity boundary's group-backed
  effective-scope resolver

#### Scenario: Missing scope is denied
- **WHEN** an authorisation policy requires a scope that is not in the user's
  effective scopes
- **THEN** the policy can deny the action without consulting direct user flags
