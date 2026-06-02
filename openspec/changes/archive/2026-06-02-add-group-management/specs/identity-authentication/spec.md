## ADDED Requirements

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
