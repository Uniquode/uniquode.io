## ADDED Requirements

### Requirement: Internal `auth_provider` boundary
The system SHALL define `auth_provider` as the Python package boundary for future OAuth2/OIDC authorisation-provider integration.

#### Scenario: Provider package naming is explicit
- **WHEN** OAuth2 provider work is planned
- **THEN** `auth_provider` is used for the Python package boundary and `fastapi-oauth-provider` is reserved for any future distribution name

#### Scenario: Provider package is independent
- **WHEN** a developer inspects the `auth_provider` boundary
- **THEN** it does not depend on FastAPI Users, `fastapi-users-auth-ext`, or `uniquode` application modules

#### Scenario: Provider contracts are host-facing
- **WHEN** the provider needs subject, client, token, grant, consent, scope, or signing-key behaviour
- **THEN** those behaviours are represented through provider-owned contracts that host applications can implement without importing host models into `auth_provider`

### Requirement: Host-owned provider configuration
The `auth_provider` boundary SHALL keep provider enablement, issuer, public mounting context, and token lifetimes under host control.

#### Scenario: Disabled provider has no runtime endpoint requirement
- **WHEN** a host application constructs default provider options
- **THEN** provider runtime endpoints remain disabled and no issuer is required

#### Scenario: Enabled provider requires issuer
- **WHEN** a host application enables the OAuth provider
- **THEN** it supplies a non-blank public issuer value

#### Scenario: Mount path is host supplied
- **WHEN** provider options are constructed
- **THEN** the public mount path is explicit and normalised before route metadata uses it

#### Scenario: Token lifetimes are configurable
- **WHEN** provider options are constructed
- **THEN** access-token, ID-token, authorisation-code, and refresh-token lifetimes are explicit positive values rather than hidden protocol defaults

### Requirement: Authlib integration layer
The `auth_provider` boundary SHALL integrate with Authlib for OAuth2/OIDC protocol machinery rather than reimplementing the protocol from scratch once runtime endpoints are implemented.

#### Scenario: Protocol work delegates to Authlib
- **WHEN** the provider needs OAuth2/OIDC protocol behaviour
- **THEN** it uses Authlib server primitives where they satisfy the requirement

#### Scenario: Project owns integration policy
- **WHEN** Authlib needs application data or policy
- **THEN** `auth_provider` supplies explicit integration interfaces for subject, client, token, grant, consent, and scope behaviour

#### Scenario: Dependency waits for runtime use
- **WHEN** only provider contracts and options are implemented
- **THEN** Authlib is not added as a runtime dependency until endpoint code directly uses it

### Requirement: OAuth token strategy
The `auth_provider` boundary SHALL encode the accepted token strategy for future OAuth2/OIDC runtime work.

#### Scenario: Access and ID token signing defaults are explicit
- **WHEN** provider token policy is inspected
- **THEN** RS256 is the default JWT signing algorithm for future access and ID token issuance

#### Scenario: Access and ID token expiry is explicit
- **WHEN** provider token policy is inspected
- **THEN** access-token and ID-token expiry values come from provider options

#### Scenario: Refresh tokens are opaque
- **WHEN** refresh-token storage policy is inspected
- **THEN** refresh tokens are represented as opaque random values with only non-recoverable server-side verifiers stored

#### Scenario: Refresh token expiry is explicit
- **WHEN** provider token policy is inspected
- **THEN** refresh-token expiry comes from provider options rather than being inferred from browser-session lifetime

#### Scenario: Refresh token rotation is single-use
- **WHEN** a refresh token is used successfully
- **THEN** the storage policy expects the presented token to be consumed and replaced by a successor in the same token family

#### Scenario: Refresh token rotation is atomic
- **WHEN** a refresh token is exchanged for a successor
- **THEN** consuming the presented token and storing the successor happen as one atomic mutation so concurrent refresh attempts cannot create multiple successors

#### Scenario: Refresh token reuse is treated as compromise
- **WHEN** a consumed refresh token is presented again
- **THEN** the storage policy expects the token family to be revoked or quarantined

#### Scenario: Subject and client refresh state can be revoked
- **WHEN** a host needs to log a subject out of one OAuth client everywhere
- **THEN** the refresh-token store can revoke all live refresh-token families for that subject/client pair without relying on browser-session state

### Requirement: Host-provided subject and scope policy
The `auth_provider` boundary SHALL obtain authenticated subjects and allowed scopes from host-provided interfaces.

#### Scenario: Subject source is external to provider
- **WHEN** the provider needs the current authenticated subject
- **THEN** it asks a host-provided subject resolver rather than importing an application user model

#### Scenario: Scope source is external to provider
- **WHEN** the provider needs to determine allowed scopes
- **THEN** it asks a host-provided scope policy rather than embedding group or flag logic

### Requirement: Deferred implementation
The system SHALL defer implementation of the internal OAuth2 provider until local users and authorisation policy are available.

#### Scenario: Identity foundation does not implement provider
- **WHEN** the identity foundation change is implemented
- **THEN** it does not implement runtime OAuth2 client administration, authorisation grants, consent flows, token issuance, introspection, or revocation endpoints

#### Scenario: Provider follows authorisation foundation
- **WHEN** provider implementation is scheduled
- **THEN** it occurs after stable local users and group, flag, and scope policy are defined
