## ADDED Requirements

### Requirement: Standalone addon package
The system SHALL introduce `fastapi-users-auth-ext` as a standalone FastAPI Users addon that is independent of the `uniquode` application.

#### Scenario: Addon does not import application code
- **WHEN** a developer inspects the addon package
- **THEN** it does not import from `uniquode` or depend on application templates, settings, models, or route modules

#### Scenario: Python package name is importable
- **WHEN** addon code is imported from Python
- **THEN** the import package uses the valid Python package name `auth_ext`

### Requirement: FastAPI Users extension boundary
The addon SHALL extend FastAPI Users through public route, dependency, user-manager, and authentication-backend integration points.

#### Scenario: Addon supplements selected flows
- **WHEN** the addon implements an advanced authentication flow
- **THEN** it uses FastAPI Users user and authentication abstractions where they fit rather than reimplementing the baseline user lifecycle

#### Scenario: Route replacement is explicit
- **WHEN** an addon flow must replace a FastAPI Users route such as login
- **THEN** the application includes the addon router intentionally instead of registering duplicate method/path combinations that depend on route-order behaviour

### Requirement: Storage-portable addon core
The addon SHALL define async storage protocols for credentials and challenges rather than coupling the core package to a specific ORM or database.

#### Scenario: Credential stores are protocol-based
- **WHEN** the addon needs to persist TOTP, WebAuthn, or recovery-code state
- **THEN** the core package depends on async storage protocols rather than application database models

#### Scenario: Storage adapters are optional
- **WHEN** a concrete storage backend is needed
- **THEN** it can be provided as an optional adapter such as SQLAlchemy, Beanie, Tortoise, Redis, or another backend without changing the addon core

### Requirement: MFA challenge flow
The addon SHALL provide a challenge flow that can pause login after successful primary authentication and complete login only after advanced authentication succeeds.

#### Scenario: User does not require challenge
- **WHEN** primary authentication succeeds and policy does not require advanced authentication
- **THEN** login completes through the configured FastAPI Users authentication backend

#### Scenario: User requires challenge
- **WHEN** primary authentication succeeds and policy requires advanced authentication
- **THEN** the addon creates short-lived challenge state instead of immediately issuing final browser authentication state

#### Scenario: Challenge completion logs user in
- **WHEN** a user completes a valid TOTP, WebAuthn, or recovery-code challenge
- **THEN** the addon completes login through the configured FastAPI Users authentication backend

### Requirement: TOTP capability
The addon SHALL define TOTP enrolment, confirmation, verification, disablement, and recovery hooks.

#### Scenario: User enrols TOTP credential
- **WHEN** an authenticated user starts TOTP enrolment
- **THEN** the addon creates pending TOTP credential state and returns the data needed by the application to display an enrolment prompt

#### Scenario: User confirms TOTP credential
- **WHEN** the user submits a valid code for pending TOTP state
- **THEN** the addon activates the TOTP credential for future advanced-authentication checks

#### Scenario: Login verifies active TOTP credential
- **WHEN** a challenged user submits a valid TOTP code
- **THEN** the addon accepts the challenge according to replay and time-window policy

### Requirement: WebAuthn passkey capability
The addon SHALL define WebAuthn/passkey registration and authentication flows around storage and challenge protocols.

#### Scenario: User starts passkey registration
- **WHEN** an authenticated user starts WebAuthn registration
- **THEN** the addon creates registration challenge state using configured relying-party settings

#### Scenario: User finishes passkey registration
- **WHEN** the browser returns a valid WebAuthn registration response
- **THEN** the addon stores the resulting credential through the configured credential store

#### Scenario: User authenticates with passkey challenge
- **WHEN** a challenged user completes a valid WebAuthn authentication ceremony
- **THEN** the addon accepts the challenge and updates stored credential state such as signature counters where required

### Requirement: UI-independent flows
The addon SHALL avoid imposing product UI assumptions.

#### Scenario: Addon routes are presentation-neutral
- **WHEN** the addon exposes routes or flow helpers
- **THEN** they return data and responses suitable for application-owned HTML pages, partials, or APIs without requiring addon-provided templates

#### Scenario: Application controls user-facing copy
- **WHEN** a flow needs user-facing text, email content, or page structure
- **THEN** the application supplies that presentation through its own templates and delivery mechanisms
