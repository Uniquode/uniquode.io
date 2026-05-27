# auth-provider Specification

## Purpose
Define the internal OAuth2/OIDC provider integration boundary and its deferral
until local identity and authorisation policy are stable.

## Requirements

### Requirement: Internal auth-provider boundary
The system SHALL define `auth-provider` as an internal package boundary for future OAuth2 authorisation-provider integration.

#### Scenario: Provider package remains internal
- **WHEN** OAuth2 provider work is planned
- **THEN** the package is treated as an internal project package rather than a generic package intended for publication

#### Scenario: Provider package is independent
- **WHEN** a developer inspects the `auth-provider` boundary
- **THEN** it does not depend on FastAPI Users, `fastapi-users-auth-ext`, or `uniquode` application modules

### Requirement: Authlib integration layer
The `auth-provider` boundary SHALL integrate with Authlib for OAuth2/OIDC protocol machinery rather than reimplementing the protocol from scratch.

#### Scenario: Protocol work delegates to Authlib
- **WHEN** the provider needs OAuth2/OIDC protocol behaviour
- **THEN** it uses Authlib server primitives where they satisfy the requirement

#### Scenario: Project owns integration policy
- **WHEN** Authlib needs application data or policy
- **THEN** `auth-provider` supplies explicit integration interfaces for subject, client, token, grant, consent, and scope behaviour

### Requirement: Host-provided subject and scope policy
The `auth-provider` boundary SHALL obtain authenticated subjects and allowed scopes from host-provided interfaces.

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
- **THEN** it does not implement OAuth2 clients, grants, consent, token issuance, introspection, or revocation endpoints

#### Scenario: Provider follows authorisation foundation
- **WHEN** provider implementation is scheduled
- **THEN** it occurs after stable local users and group, flag, and scope policy are defined
