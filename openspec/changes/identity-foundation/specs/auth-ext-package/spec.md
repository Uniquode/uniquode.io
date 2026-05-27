## ADDED Requirements

### Requirement: Reusable FastAPI `auth_ext` package
The system SHALL expand `auth_ext` into a reusable identity and authentication
package that is independent of the `uniquode` application and suitable for use
by other FastAPI applications.

#### Scenario: Package does not import host application code
- **WHEN** a developer inspects the `auth_ext` package
- **THEN** it does not import from `uniquode` or depend on application
  templates, settings, models, persistence modules, or route modules

#### Scenario: Package owns identity and authentication contracts
- **WHEN** identity models, service APIs, options/config objects, or persistence
  protocols are needed
- **THEN** those contracts are defined by `auth_ext` rather than by the host
  application

#### Scenario: Host application integrates package
- **WHEN** `uniquode` needs identity capabilities
- **THEN** it imports and configures `auth_ext` as a host application
  rather than being imported by the package

### Requirement: FastAPI Users integration boundary
The `auth_ext` package SHALL integrate with FastAPI Users through public route,
dependency, user-manager, and authentication-backend integration points.

#### Scenario: Package uses FastAPI Users baseline primitives
- **WHEN** baseline local identity behaviour is implemented
- **THEN** the package uses FastAPI Users abstractions where they fit rather
  than reimplementing account lifecycle primitives unnecessarily

#### Scenario: Package owns host-facing API
- **WHEN** FastAPI Users provides lower-level primitives
- **THEN** `auth_ext` exposes stable host-facing services, options,
  and integration helpers rather than requiring hosts to depend on private
  FastAPI Users details

#### Scenario: Route replacement is explicit
- **WHEN** an `auth_ext` flow must replace a FastAPI Users route such as
  login
- **THEN** the host application includes the package router intentionally
  instead of registering duplicate method/path combinations that depend on
  route-order behaviour

### Requirement: Storage-portable identity core
The `auth_ext` package SHALL define async storage protocols and optional adapters
rather than coupling its core to a specific host application database module.

#### Scenario: Identity stores are protocol-based
- **WHEN** the package needs to persist users, sessions, OAuth links, TOTP,
  WebAuthn, recovery-code, or challenge state
- **THEN** the package core depends on `auth_ext` async protocols rather
  than host application database models

#### Scenario: Storage adapters are optional
- **WHEN** a concrete storage backend is needed
- **THEN** it can be provided as an adapter such as SQLAlchemy, Beanie, Tortoise,
  Redis, or another backend without changing the package core

#### Scenario: SQLAlchemy adapter is first-class
- **WHEN** the first host integration is implemented
- **THEN** the package provides or supports a SQLAlchemy async adapter suitable
  for SQLite and PostgreSQL

### Requirement: Advanced authentication extension points
The `auth_ext` package SHALL define extension points for MFA and advanced
authentication without requiring those features in the first structural slice.

#### Scenario: MFA challenge can pause login
- **WHEN** primary authentication succeeds and policy requires advanced
  authentication
- **THEN** the package can create short-lived challenge state instead of
  immediately issuing final browser authentication state

#### Scenario: Challenge completion can finish login
- **WHEN** a user completes a valid TOTP, WebAuthn, or recovery-code challenge
- **THEN** the package can complete login through the configured FastAPI Users
  authentication backend

#### Scenario: Advanced credential storage remains portable
- **WHEN** TOTP, WebAuthn, or recovery-code state is introduced
- **THEN** storage uses package-owned protocols and adapters rather than host
  application models

### Requirement: UI-independent flows
The `auth_ext` package SHALL avoid imposing product UI assumptions.

#### Scenario: Package routes are presentation-neutral
- **WHEN** the package exposes routes or flow helpers
- **THEN** they return data and responses suitable for application-owned HTML
  pages, partials, or APIs without requiring package-provided product templates

#### Scenario: Host controls user-facing copy
- **WHEN** a flow needs user-facing text, email content, or page structure
- **THEN** the host application supplies presentation through its own templates
  and delivery mechanisms
