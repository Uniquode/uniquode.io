# authorisation-model Specification

## Purpose
Define the reusable authorisation model for groups, scopes, group membership,
nested group membership, effective-scope resolution, and runtime cache
invalidation. CLI management commands are specified by `auth-management-cli`.
## Requirements
### Requirement: Authorisation groups
The system SHALL provide groups as reusable authorisation capability containers
owned by the identity/auth extension boundary.

#### Scenario: Group stores stable identity and operator metadata
- **WHEN** an authorisation group is created
- **THEN** the group stores a stable ID, a unique immutable abbreviation, and an
  operator-facing description

#### Scenario: Group abbreviation is unique
- **WHEN** an operator creates a group with an abbreviation already used by
  another group
- **THEN** the operation fails without creating a duplicate group

#### Scenario: Group abbreviation is immutable
- **WHEN** an operator updates an existing group
- **THEN** the operation does not allow changing the group's abbreviation

### Requirement: Described scopes
The system SHALL store scopes as described records that can be assigned to
groups.

#### Scenario: Scope record stores description
- **WHEN** an operator creates a scope
- **THEN** the scope stores its stable string value and optional descriptive text

#### Scenario: Scope strings remain unconstrained
- **WHEN** an operator creates a scope
- **THEN** the system does not require the scope string to match a configured
  prefix or naming pattern

#### Scenario: Duplicate scope is rejected
- **WHEN** an operator creates a scope with a string that already exists
- **THEN** the operation fails without creating a duplicate scope record

### Requirement: Group scope assignment
The system SHALL allow scopes to be assigned to groups without allowing duplicate
assignments within the same group.

#### Scenario: Group receives scope
- **WHEN** an operator assigns an existing scope to a group
- **THEN** members of that group can receive that scope through effective-scope
  resolution

#### Scenario: Duplicate group scope is rejected
- **WHEN** an operator assigns a scope to a group that already has that scope
- **THEN** the operation fails without creating a duplicate group-scope
  assignment

#### Scenario: Shared scope is allowed across groups
- **WHEN** two different groups are assigned the same scope
- **THEN** both assignments are valid and effective-scope resolution folds the
  duplicated scope into a single effective scope value

### Requirement: Group membership graph
The system SHALL allow groups to contain users and other groups while preserving
an acyclic group graph.

#### Scenario: User is assigned to group
- **WHEN** an operator assigns a user to a group
- **THEN** the user becomes a direct member of that group

#### Scenario: Duplicate user membership is rejected
- **WHEN** an operator assigns a user to a group that already contains that user
- **THEN** the operation fails without creating a duplicate membership

#### Scenario: Group is assigned to group
- **WHEN** an operator assigns one group as a child of another group
- **THEN** members of the parent group can receive scopes from the child group
  through recursive effective-scope resolution

#### Scenario: Duplicate group membership is rejected
- **WHEN** an operator assigns a child group to a parent group that already
  contains that child group
- **THEN** the operation fails without creating a duplicate nested group
  membership

#### Scenario: Self membership is rejected
- **WHEN** an operator attempts to add a group as its own child
- **THEN** the operation fails without changing group membership

#### Scenario: Cyclic membership is rejected
- **WHEN** an operator attempts to add a nested group relationship that would
  create a cycle
- **THEN** the operation fails without changing group membership

#### Scenario: Selection excludes cyclic choices
- **WHEN** the system presents candidate child groups for a parent group
- **THEN** it includes only groups that are not already seen in the parent
  group's reachable graph and would not create a cycle

### Requirement: Effective scope resolution
The system SHALL resolve a user's effective scopes by recursively traversing
direct and nested group membership.

#### Scenario: Direct group scopes are resolved
- **WHEN** a user is a direct member of a group with assigned scopes
- **THEN** effective-scope resolution includes that group's scopes

#### Scenario: Nested group scopes are resolved
- **WHEN** a user is a member of a group that contains another group
- **THEN** effective-scope resolution includes scopes from the reachable nested
  group

#### Scenario: Duplicate scopes are folded
- **WHEN** a user reaches the same scope through more than one group
- **THEN** effective-scope resolution returns that scope only once

#### Scenario: Group is processed once
- **WHEN** effective-scope resolution traverses group membership
- **THEN** it never processes the same group more than once

#### Scenario: User has no direct scopes
- **WHEN** a user has no group membership
- **THEN** effective-scope resolution returns no scopes for that user

### Requirement: Runtime effective-scope cache
The system SHALL cache effective-scope resolution at runtime and rebuild cached
results on demand after authorisation mutations.

#### Scenario: Effective scopes are cached
- **WHEN** effective scopes are resolved for a user
- **THEN** the result can be reused from a runtime cache for later checks in the
  same process

#### Scenario: Cache is invalidated by membership changes
- **WHEN** user-group or group-group membership changes
- **THEN** cached effective-scope results affected by group membership are
  invalidated before later checks use them

#### Scenario: Cache is invalidated by scope changes
- **WHEN** a scope record or group-scope assignment changes
- **THEN** cached effective-scope results affected by scope assignment are
  invalidated before later checks use them

#### Scenario: Cache is not persisted
- **WHEN** the application restarts
- **THEN** effective-scope cache entries are rebuilt on demand rather than loaded
  from persisted cache state

### Requirement: Group deletion safety
The system SHALL refuse to delete groups that still participate in membership
relationships.

#### Scenario: Delete group with users is rejected
- **WHEN** an operator attempts to delete a group that contains users
- **THEN** the operation fails without deleting the group

#### Scenario: Delete group with child groups is rejected
- **WHEN** an operator attempts to delete a group that contains child groups
- **THEN** the operation fails without deleting the group

#### Scenario: Delete group with parent groups is rejected
- **WHEN** an operator attempts to delete a group that is contained by another
  group
- **THEN** the operation fails without deleting the group

#### Scenario: Delete empty group succeeds
- **WHEN** an operator deletes a group with no user, child group, or parent group
  memberships
- **THEN** the group is removed without changing users or other groups
