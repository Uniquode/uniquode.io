# auth-ext-package Specification

## Purpose
Define the reusable `wybra.auth` identity and authentication package boundary for
local identity, FastAPI Users integration, storage portability, and future
advanced authentication extension points.

## Requirements

### Requirement: Reusable FastAPI `wybra.auth` package
The system SHALL expand `wybra.auth` into a reusable identity and authentication
package that is independent of the `uniquode` application and suitable for use
by other FastAPI applications.

#### Scenario: Package is incubated in repository
- **WHEN** `wybra.auth` is developed before standalone publication
- **THEN** it can remain inside the current source tree while preserving an API
  shape suitable for later extraction as `fastapi-users-auth-ext`

#### Scenario: Package does not import host application code
- **WHEN** a developer inspects the `wybra.auth` package
- **THEN** it does not import from `uniquode` or depend on application
  templates, settings, models, persistence modules, or route modules

#### Scenario: Package owns identity and authentication contracts
- **WHEN** identity models, service APIs, options/config objects, or persistence
  protocols are needed
- **THEN** those contracts are defined by `wybra.auth` rather than by the host
  application

#### Scenario: Public API avoids adapter leakage
- **WHEN** host applications import from the top-level `wybra.auth` package
- **THEN** the exported API favours host-facing, storage-agnostic concepts and
  does not expose SQLAlchemy-specific implementation details unless a current
  integration requirement forces that exposure

#### Scenario: Host application integrates package
- **WHEN** `uniquode` needs identity capabilities
- **THEN** it imports and configures `wybra.auth` as a host application
  rather than being imported by the package

### Requirement: FastAPI Users integration boundary
The `wybra.auth` package SHALL integrate with FastAPI Users through public route,
dependency, user-manager, and authentication-backend integration points.

#### Scenario: Package uses FastAPI Users baseline primitives
- **WHEN** baseline local identity behaviour is implemented
- **THEN** the package uses FastAPI Users abstractions where they fit rather
  than reimplementing account lifecycle primitives unnecessarily

#### Scenario: Package owns host-facing API
- **WHEN** FastAPI Users provides lower-level primitives
- **THEN** `wybra.auth` exposes stable host-facing services, options,
  and integration helpers rather than requiring hosts to depend on private
  FastAPI Users details

#### Scenario: Flow results are presentation-neutral
- **WHEN** `wybra.auth` exposes flow helpers for authentication or account
  lifecycle behaviour
- **THEN** those helpers return package-owned outcomes or values that do not
  depend on templates, redirects, htmx, or JSON response formats

#### Scenario: Route replacement is explicit
- **WHEN** an `wybra.auth` flow must replace a FastAPI Users route such as
  login
- **THEN** the host application includes the package router intentionally
  instead of registering duplicate method/path combinations that depend on
  route-order behaviour

### Requirement: Storage-portable identity core
The `wybra.auth` package SHALL define async storage protocols and optional adapters
rather than coupling its core to a specific host application database module.

#### Scenario: Identity stores are protocol-based
- **WHEN** the package needs to persist users, sessions, OAuth links, TOTP,
  WebAuthn, recovery-code, or challenge state
- **THEN** the package core depends on `wybra.auth` async protocols rather
  than host application database models

#### Scenario: Storage adapters are optional
- **WHEN** a concrete storage backend is needed
- **THEN** it can be provided as an adapter such as SQLAlchemy, Beanie, Tortoise,
  Redis, or another backend without changing the package core

#### Scenario: SQLAlchemy adapter is first-class
- **WHEN** the first host integration is implemented
- **THEN** the package provides or supports a SQLAlchemy async adapter suitable
  for SQLite and PostgreSQL

#### Scenario: SQLAlchemy is not the core abstraction
- **WHEN** package core code needs storage access
- **THEN** it depends on narrow `wybra.auth` contracts where practical, while
  SQLAlchemy-specific models and helpers remain in the SQLAlchemy adapter
  boundary

### Requirement: Advanced authentication extension points
The `wybra.auth` package SHALL define extension points for MFA and advanced
authentication without requiring those features in the first structural slice.

#### Scenario: Authentication ceremony can remain incomplete
- **WHEN** an authentication ceremony has a successful password, passkey,
  provider, or recovery step but policy still requires another authenticator
- **THEN** the package can represent the next required step instead of
  immediately issuing final browser authentication state

#### Scenario: Challenge completion can finish ceremony
- **WHEN** a user completes a valid TOTP, WebAuthn, or recovery-code challenge
- **THEN** the package can complete the authentication ceremony through the
  configured FastAPI Users authentication backend when policy requirements are
  satisfied

#### Scenario: Passkey can be a login-screen authenticator
- **WHEN** WebAuthn/passkey support is enabled
- **THEN** the package can expose passkey challenge state that a host login
  surface can offer before or instead of password entry where policy allows

#### Scenario: Advanced credential storage remains portable
- **WHEN** TOTP, WebAuthn, or recovery-code state is introduced
- **THEN** storage uses package-owned protocols and adapters rather than host
  application models

### Requirement: UI-independent flows
The `wybra.auth` package SHALL avoid imposing product UI assumptions.

#### Scenario: Package routes are presentation-neutral
- **WHEN** the package exposes routes or flow helpers
- **THEN** they return data and responses suitable for application-owned HTML
  pages, partials, or APIs without requiring package-provided product templates

#### Scenario: Host controls user-facing copy
- **WHEN** a flow needs user-facing text, email content, or page structure
- **THEN** the host application supplies presentation through its own templates
  and delivery mechanisms

#### Scenario: Package templates are deferred
- **WHEN** reusable package-owned base templates are considered
- **THEN** they are deferred until a later template-engine/module override
  change defines how independent modules provide defaults and host
  applications override them
