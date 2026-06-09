# fastapi-users-auth-ext Specification

## Purpose
Define the standalone FastAPI Users authentication extension boundary for
advanced authentication features such as MFA, TOTP, WebAuthn/passkeys, and
recovery flows.
## Requirements
### Requirement: Standalone addon package
The system SHALL introduce `fastapi-users-auth-ext` as a standalone FastAPI
Users addon that is independent of the `uniquode` application while allowing
the addon to publish optional configured-module surfaces.

#### Scenario: Addon does not import application code
- **WHEN** a developer inspects the addon package
- **THEN** it does not import from `uniquode` or depend on application
  templates, settings, models, route modules, static assets, or product context
  providers

#### Scenario: Addon may depend on core contracts
- **WHEN** the addon publishes configured-module surfaces
- **THEN** it may depend on `wevra.web` contracts for web surfaces and
  `wevra.db` contracts for model metadata rather than importing the
  `uniquode` application package

#### Scenario: Addon can publish model metadata
- **WHEN** the addon owns reusable identity persistence models
- **THEN** those models are exposed through the configured-module model metadata
  convention rather than through an application-owned model list

#### Scenario: Addon can publish migration revisions
- **WHEN** the addon owns reusable identity persistence models
- **THEN** migration revisions for those models are bundled alongside the addon
  and included only when the addon module is configured

#### Scenario: Addon can publish package templates
- **WHEN** the addon owns reusable identity page or partial defaults
- **THEN** those templates are packaged under the addon and exposed through the
  host application's template-source composition mechanism

#### Scenario: Addon can publish package static assets
- **WHEN** the addon owns reusable identity static assets
- **THEN** those assets are packaged under the addon and exposed through the
  host application's static-source composition mechanism

#### Scenario: Python package name is importable
- **WHEN** addon code is imported from Python
- **THEN** the import package uses the valid Python package name `wevra.auth`

### Requirement: FastAPI Users extension boundary
The addon SHALL extend FastAPI Users through public route, dependency,
user-manager, authentication-backend, and application-module composition
integration points.

#### Scenario: Addon supplements selected flows
- **WHEN** the addon implements an advanced authentication flow
- **THEN** it uses FastAPI Users user and authentication abstractions where they fit rather than reimplementing the baseline user lifecycle

#### Scenario: Route replacement is explicit
- **WHEN** an addon flow must replace a FastAPI Users route such as login
- **THEN** the application installs the addon module or router intentionally
  instead of registering duplicate method/path combinations that depend on
  route-order behaviour

#### Scenario: Addon publishes identity route module
- **WHEN** the addon provides reusable identity pages, partials, or APIs
- **THEN** it exposes them through a configured module route surface rather than
  by mutating the host application automatically

#### Scenario: Addon can be omitted from composition
- **WHEN** the host application omits `wevra.auth` from `modules`
- **THEN** the addon contributes no models, migration revisions, routes,
  templates, static assets, or context providers to that application instance

### Requirement: Storage-portable addon core
The addon SHALL define async storage protocols for external-provider identities
and ceremony-linked challenge metadata rather than coupling the core package to a
specific ORM or database.

#### Scenario: Linked-provider store is protocol-based
- **WHEN** the addon persists linked provider identities and callback state
- **THEN** the core package depends on protocol interfaces rather than the
  application ORM type directly

#### Scenario: Optional storage adapters are supported
- **WHEN** a concrete storage backend is required
- **THEN** optional adapters (for example SQLAlchemy, Beanie, Tortoise, Redis)
  can be attached without changing the addon contracts

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
The addon SHALL avoid imposing product UI assumptions while allowing reusable
default identity templates and static assets to be overridden by the host
application.

#### Scenario: Addon routes are host-enabled
- **WHEN** the addon exposes routes or flow helpers
- **THEN** the host application includes those routes intentionally and remains
  in control of where they are mounted

#### Scenario: Addon templates do not own product shell
- **WHEN** the addon ships default identity templates
- **THEN** those templates render identity content and forms without owning web
  foundation theme defaults, branding, product navigation, or layout chrome

#### Scenario: Application can override addon templates
- **WHEN** the application supplies a template at the same logical path as an
  addon default
- **THEN** the application template is used instead of the addon template

#### Scenario: Application can override addon static assets
- **WHEN** the application supplies a static asset at the same logical path as
  an addon default
- **THEN** the application static asset is served instead of the addon asset

#### Scenario: Application controls user-facing product policy
- **WHEN** a flow needs deployment-specific page copy, email content, redirects,
  delivery integration, throttling, or product policy
- **THEN** the application supplies that policy or override through the addon
  configuration and application-composition boundaries

### Requirement: Shared ownership of storage contracts
The addon SHALL provide protocol types in `wevra` so applications consume the
link and assertion contracts without adding new schema ownership or provider
persistence tables themselves.

#### Scenario: Host application uses shared contracts
- **WHEN** a host application needs provider-linking persistence and assertion
  flows
- **THEN** the application uses the shared wevra contracts and does not define
  its own provider identity table schema in this change

### Requirement: Provider-identity contracts
The addon SHALL define clear protocol types and errors for provider identity
lookup, linking, unlinking, and callback assertion persistence.

#### Scenario: Provider identity link is stored and resolved
- **WHEN** a valid provider link is created for an authenticated local user
- **THEN** the addon stores provider name and subject and can resolve the same
  link to that local user

#### Scenario: Provider identity callbacks are represented as assertions
- **WHEN** a provider callback returns a verifiable assertion
- **THEN** the addon converts it into a ceremony assertion rather than writing
  session state directly

#### Scenario: Link collisions are surfaced as branchable results
- **WHEN** provider identity linkage is attempted for an already linked subject
- **THEN** the addon returns a branchable conflict result instead of silently
  reassigning ownership

### Requirement: Shared ceremony bridge
The addon SHALL bridge provider-linked assertions into the host ceremony surface
consistently with existing inactive-account and session policies, resolving local
user principals through the shared email ownership relation before assertion
finalisation.

#### Scenario: Provider-linked users are ineligible when inactive
- **WHEN** local account checks fail for inactivity or effective expiry after email
  resolution
- **THEN** the addon rejects completion and emits a branchable inactive result

#### Scenario: Provider assertion does not bypass final ceremony policy
- **WHEN** a provider assertion succeeds but configured policy requires a further
  assertion
- **THEN** the addon keeps the ceremony incomplete until policy is satisfied

#### Scenario: Ceremony principal is resolved before provider completion
- **WHEN** a provider callback includes an email claim that maps to a local user
  via `identity_user_email`
- **THEN** the addon resolves that user first and applies the callback to the same
  user context

