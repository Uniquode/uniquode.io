## ADDED Requirements

### Requirement: Third-party provider enablement
The system SHALL expose third-party OAuth/OIDC login and linking flows only for
providers explicitly enabled by host configuration.

#### Scenario: Provider disabled hides provider routes
- **WHEN** a provider such as Google, Apple, GitHub, Facebook, or LinkedIn is
  disabled
- **THEN** the system does not expose that provider as a login or account-linking
  choice

#### Scenario: Provider enabled requires configuration
- **WHEN** a provider is enabled
- **THEN** the system requires provider configuration such as client ID, client
  secret where applicable, scopes, callback path, trusted issuer or discovery
  metadata, and claim mapping

#### Scenario: Misconfigured provider fails startup or validation
- **WHEN** an enabled provider has missing or invalid required configuration
- **THEN** startup or validation fails before that provider is exposed

### Requirement: Third-party OAuth login ceremony
The system SHALL allow successful external-provider callbacks to participate in
the local authentication ceremony without replacing the local user account.

#### Scenario: Provider callback resolves linked user
- **WHEN** a provider callback is valid and maps to an existing linked provider
  identity
- **THEN** the system resolves the associated local user account and records a
  provider assertion for the ceremony

#### Scenario: Provider login creates account only by policy
- **WHEN** a provider callback is valid but no linked local user exists
- **THEN** the system creates a local account only when account-creation policy
  explicitly allows that provider and login context

#### Scenario: Provider assertion does not always complete login
- **WHEN** a provider assertion is accepted
- **THEN** the ceremony issues final browser session state only if the configured
  ceremony policy is satisfied

#### Scenario: Inactive linked user cannot login
- **WHEN** a valid provider callback maps to an inactive or effectively expired
  local user
- **THEN** the ceremony rejects login and does not issue browser session state

### Requirement: Provider identity linking
The system SHALL link external provider identities to local user accounts
through authenticated, policy-controlled flows.

#### Scenario: Authenticated user starts linking
- **WHEN** an authenticated user starts linking an enabled provider
- **THEN** the system creates provider authorisation state tied to that local
  user and provider

#### Scenario: Provider identity links by provider subject
- **WHEN** a linking callback succeeds
- **THEN** the system links the local user to the provider using provider name
  and provider subject identifier as the stable identity key

#### Scenario: Already linked provider identity is rejected
- **WHEN** a provider subject identifier is already linked to another local user
- **THEN** the system rejects the linking attempt

#### Scenario: Email alone does not prove linking ownership
- **WHEN** a provider supplies an email claim
- **THEN** the system does not treat that email alone as proof that the provider
  identity can be linked to an existing local account

### Requirement: Provider identity unlinking
The system SHALL allow unlinking provider identities while preserving account
access and policy invariants.

#### Scenario: User unlinks provider identity
- **WHEN** an authenticated user unlinks one of their linked provider identities
- **THEN** that provider identity can no longer authenticate or satisfy login
  ceremony policy for the account

#### Scenario: Administrator unlinks provider identity
- **WHEN** an authorised administrator unlinks a provider identity from a user
- **THEN** that provider identity can no longer authenticate or satisfy login
  ceremony policy for the account

#### Scenario: Unlink cannot remove last usable method by default
- **WHEN** unlinking a provider identity would leave a user without any
  permitted login or recovery method
- **THEN** the system rejects unlinking unless explicit administrative recovery
  policy allows it

### Requirement: Provider identity lifecycle
The system SHALL manage external provider identity records independently from
user profile fields.

#### Scenario: Provider subject is canonical link key
- **WHEN** provider identity data is stored
- **THEN** provider name and provider subject identifier form the stable link key
  rather than display name or email address

#### Scenario: Provider claims can update metadata
- **WHEN** a linked provider login succeeds
- **THEN** the system can update non-authoritative provider metadata such as
  display claims, email claim, avatar URL, or last-used timestamp without
  replacing the local user profile by default

#### Scenario: Provider tokens are protected
- **WHEN** provider access tokens, refresh tokens, ID tokens, or token metadata
  are stored
- **THEN** the system stores them according to configured secret-protection and
  retention policy and never exposes them through templates or public APIs

### Requirement: Provider callback security
The system SHALL validate provider callback state and token responses before any
local ceremony assertion, account creation, or linking action is performed.

#### Scenario: Invalid OAuth state is rejected
- **WHEN** a provider callback has missing, expired, mismatched, or replayed
  state
- **THEN** the system rejects the callback without linking an account or issuing
  browser session state

#### Scenario: Invalid provider token response is rejected
- **WHEN** a provider token response or ID token fails configured provider
  validation
- **THEN** the system rejects the callback without linking an account or issuing
  browser session state

#### Scenario: Provider-specific claims are mapped explicitly
- **WHEN** a provider callback succeeds
- **THEN** the system maps provider claims through configured provider-specific
  claim rules rather than assuming all providers use the same claim semantics
