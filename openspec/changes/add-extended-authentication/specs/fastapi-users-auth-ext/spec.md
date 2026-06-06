## MODIFIED Requirements

### Requirement: Storage-portable addon core
The addon SHALL define async storage protocols for credentials, challenges, and
linked provider identities rather than coupling the core package to a specific
ORM or database.

#### Scenario: Credential stores are protocol-based
- **WHEN** the addon needs to persist TOTP, WebAuthn, recovery-code, challenge,
  or linked external-provider state
- **THEN** the core package depends on async storage protocols rather than
  application database models

#### Scenario: Storage adapters are optional
- **WHEN** a concrete storage backend is needed
- **THEN** it can be provided as an optional adapter such as SQLAlchemy, Beanie,
  Tortoise, Redis, or another backend without changing the addon core

#### Scenario: SQLAlchemy adapter follows model package convention
- **WHEN** the addon ships SQLAlchemy ORM models for extended authentication
  credentials or linked provider identities
- **THEN** those models live under `wevra.auth.models` and expose Alembic-ready
  metadata for explicit host inclusion

### Requirement: MFA challenge flow
The addon SHALL provide an authentication ceremony flow that can collect
password, TOTP, recovery-code, WebAuthn/passkey, or external-provider
assertions and complete login only after configured policy succeeds.

#### Scenario: User does not require challenge
- **WHEN** primary authentication or another trusted assertion succeeds and
  policy does not require additional authentication
- **THEN** login completes through the configured FastAPI Users authentication
  backend

#### Scenario: User requires challenge
- **WHEN** an assertion succeeds but policy requires additional authentication
- **THEN** the addon creates short-lived challenge state or returns the next
  required ceremony methods instead of immediately issuing final browser
  authentication state

#### Scenario: Challenge completion logs user in
- **WHEN** a user completes a valid TOTP, WebAuthn, recovery-code, or
  provider-backed challenge and all policy requirements are satisfied
- **THEN** the addon completes login through the configured FastAPI Users
  authentication backend

#### Scenario: Inactive user cannot complete challenge
- **WHEN** the local user becomes inactive or effectively expired before
  ceremony completion
- **THEN** the addon rejects the ceremony and does not issue browser
  authentication state

### Requirement: TOTP capability
The addon SHALL define TOTP enrolment, confirmation, verification, disablement,
and reset hooks.

#### Scenario: User enrols TOTP credential
- **WHEN** an authenticated user starts TOTP enrolment
- **THEN** the addon creates pending TOTP credential state and returns the data
  needed by the application to display an enrolment prompt

#### Scenario: User confirms TOTP credential
- **WHEN** the user submits a valid code for pending TOTP state
- **THEN** the addon activates the TOTP credential for future
  advanced-authentication checks

#### Scenario: Login verifies active TOTP credential
- **WHEN** a challenged user submits a valid TOTP code
- **THEN** the addon accepts the challenge according to replay and time-window
  policy

#### Scenario: User disables TOTP credential
- **WHEN** an authenticated user or authorised administrator satisfies
  disablement policy
- **THEN** the addon disables the TOTP credential so it can no longer satisfy a
  login ceremony

#### Scenario: User resets TOTP credential
- **WHEN** an authenticated user or authorised administrator resets TOTP for an
  account
- **THEN** the addon invalidates the existing active TOTP credential and
  requires new enrolment before TOTP can satisfy ceremony policy again

### Requirement: WebAuthn passkey capability
The addon SHALL define WebAuthn/passkey registration, authentication, and
credential revocation flows around storage and challenge protocols.

#### Scenario: User starts passkey registration
- **WHEN** an authenticated user starts WebAuthn registration
- **THEN** the addon creates registration challenge state using configured
  relying-party settings

#### Scenario: User finishes passkey registration
- **WHEN** the browser returns a valid WebAuthn registration response
- **THEN** the addon stores the resulting credential through the configured
  credential store

#### Scenario: User authenticates with passkey challenge
- **WHEN** a challenged user completes a valid WebAuthn authentication ceremony
- **THEN** the addon accepts the challenge and updates stored credential state
  such as signature counters where required

#### Scenario: User revokes passkey credential
- **WHEN** an authenticated user or authorised administrator revokes a WebAuthn
  credential
- **THEN** the addon prevents that credential from satisfying future ceremony
  policy

## ADDED Requirements

### Requirement: Recovery-code capability
The addon SHALL define recovery-code generation, storage, consumption,
regeneration, and revocation flows around one-time verifier storage.

#### Scenario: User generates recovery-code set
- **WHEN** an eligible authenticated user requests recovery codes
- **THEN** the addon creates a new one-time recovery-code set and returns the
  plaintext codes only in the generation response

#### Scenario: Recovery code completes challenge
- **WHEN** a challenged user submits a valid unused recovery code
- **THEN** the addon consumes the code exactly once and records the recovery
  assertion for the ceremony

#### Scenario: Recovery-code regeneration revokes old codes
- **WHEN** a user regenerates recovery codes
- **THEN** the addon atomically revokes the previous recovery-code set and
  creates a new set

### Requirement: Third-party OAuth client capability
The addon SHALL define third-party OAuth/OIDC client login, account linking,
unlinking, and linked provider identity storage around the canonical local user
model.

#### Scenario: Provider callback participates in ceremony
- **WHEN** an enabled provider returns a valid callback for a linked identity
- **THEN** the addon records a provider assertion for the local user's
  authentication ceremony

#### Scenario: Provider identity links to local user
- **WHEN** an authenticated user completes a provider linking flow
- **THEN** the addon links provider name and provider subject identifier to that
  local user

#### Scenario: Provider identity unlinks from local user
- **WHEN** an authenticated user or authorised administrator unlinks a provider
  identity
- **THEN** the addon prevents that provider identity from authenticating the
  local user in future ceremonies
