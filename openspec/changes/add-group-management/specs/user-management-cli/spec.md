## ADDED Requirements

### Requirement: Group management commands
The `usermgr` command SHALL provide local group and scope management commands
through the existing auth configuration and database boundaries.

#### Scenario: Group command tree exists
- **WHEN** an operator runs `usermgr group --help`
- **THEN** the command lists group create, update, delete, list, show,
  membership, scope, and effective-scope operations

#### Scenario: Scope command tree exists
- **WHEN** an operator runs `usermgr scope --help`
- **THEN** the command lists scope create, update, delete, and list operations

#### Scenario: Group commands use existing configuration
- **WHEN** an operator supplies `--config path/to/auth.toml` or
  `AUTH_DATABASE_URL` for a group or scope command
- **THEN** the command uses the same effective identity configuration and
  database resolution as existing user commands

### Requirement: Group target resolution
The `usermgr` command SHALL resolve group command targets by stable group ID or
unique group abbreviation.

#### Scenario: Group abbreviation target is supplied
- **WHEN** an operator supplies a group target matching an existing abbreviation
- **THEN** the command resolves the target to that group

#### Scenario: Group identifier target is supplied
- **WHEN** an operator supplies a group target matching an existing group ID
- **THEN** the command resolves the target to that group

#### Scenario: Unknown group target is supplied
- **WHEN** an operator supplies a group target that matches no group ID or
  abbreviation
- **THEN** the command fails with an invalid group target error

### Requirement: Group lifecycle operations
The `usermgr` command SHALL allow operators to create, inspect, update, list,
and delete groups safely.

#### Scenario: Create group
- **WHEN** an operator runs `usermgr group create <abbrev>` with a description
  and one or more scopes
- **THEN** the command creates a group with a stable ID, immutable abbreviation,
  description, and scope assignments

#### Scenario: Update group description
- **WHEN** an operator runs `usermgr group <id-or-abbrev> update` with a new
  description
- **THEN** the command updates the group description without changing the group
  abbreviation

#### Scenario: List groups
- **WHEN** an operator runs `usermgr group list`
- **THEN** the command emits group records in human-readable output by default
  and supports JSON or CSV output when requested

#### Scenario: Show group
- **WHEN** an operator runs `usermgr group <id-or-abbrev> show`
- **THEN** the command shows the group's ID, abbreviation, description, scopes,
  user memberships, child groups, and parent groups

#### Scenario: Delete group with memberships is rejected
- **WHEN** an operator runs `usermgr group <id-or-abbrev> delete` for a group
  that has users, child groups, or parent groups
- **THEN** the command fails without deleting the group

### Requirement: Scope lifecycle operations
The `usermgr` command SHALL allow operators to create, update, and list scope
records with optional descriptive text.

#### Scenario: Create scope
- **WHEN** an operator runs `usermgr scope create <scope> --description <text>`
- **THEN** the command creates the scope record with the supplied description

#### Scenario: Update scope description
- **WHEN** an operator runs `usermgr scope update <scope> --description <text>`
- **THEN** the command updates the scope description without changing the scope
  string

#### Scenario: Delete unused scope
- **WHEN** an operator runs `usermgr scope delete <scope>` for a scope that is not
  assigned to any group
- **THEN** the command removes the scope record

#### Scenario: Delete used scope is rejected
- **WHEN** an operator runs `usermgr scope delete <scope>` for a scope assigned to
  one or more groups
- **THEN** the command fails without removing the scope record

#### Scenario: List scopes
- **WHEN** an operator runs `usermgr scope list`
- **THEN** the command emits scope records in human-readable output by default
  and supports JSON or CSV output when requested

### Requirement: Group membership operations
The `usermgr` command SHALL allow operators to assign and remove user and nested
group membership while preventing duplicates and cycles.

#### Scenario: Add user to group
- **WHEN** an operator runs `usermgr group <id-or-abbrev> add-user <user-target>`
- **THEN** the command adds the target user to the group

#### Scenario: Remove user from group
- **WHEN** an operator runs `usermgr group <id-or-abbrev> remove-user <user-target>`
- **THEN** the command removes the target user from the group

#### Scenario: Add child group
- **WHEN** an operator runs `usermgr group <parent-id-or-abbrev> add-group
  <child-id-or-abbrev>`
- **THEN** the command adds the child group to the parent group when the
  relationship does not create a duplicate or cycle

#### Scenario: Remove child group
- **WHEN** an operator runs `usermgr group <parent-id-or-abbrev> remove-group
  <child-id-or-abbrev>`
- **THEN** the command removes the child group from the parent group

#### Scenario: Cyclic child group is rejected
- **WHEN** an operator attempts to add a child group that would create a cycle
- **THEN** the command fails without changing group membership

### Requirement: User group membership options
The `usermgr` command SHALL support group membership while creating or updating
users.

#### Scenario: Create user with groups
- **WHEN** an operator runs `usermgr create <email> --group <id-or-abbrev>` one
  or more times
- **THEN** the command creates the user and assigns the user to the supplied
  groups

#### Scenario: Add group to user
- **WHEN** an operator runs `usermgr update <user-target> --add-group
  <id-or-abbrev>`
- **THEN** the command adds the user to that group without replacing other group
  memberships

#### Scenario: Remove group from user
- **WHEN** an operator runs `usermgr update <user-target> --rm-group
  <id-or-abbrev>`
- **THEN** the command removes the user from that group without changing other
  group memberships

#### Scenario: Set user groups
- **WHEN** an operator runs `usermgr update <user-target> --set-group
  <id-or-abbrev>` one or more times
- **THEN** the command replaces the user's direct group memberships with exactly
  the supplied groups

#### Scenario: Group replacement is explicit
- **WHEN** an operator runs `usermgr update <user-target> --group
  <id-or-abbrev>`
- **THEN** the command rejects the option because replacement uses `--set-group`
  and incremental updates use `--add-group` or `--rm-group`

### Requirement: Effective scope inspection
The `usermgr` command SHALL allow operators to inspect effective scopes for a
user target.

#### Scenario: Show effective scopes
- **WHEN** an operator runs `usermgr group effective-scopes <user-target>`
- **THEN** the command prints the de-duplicated scopes resolved through direct
  and nested group membership

#### Scenario: Effective scopes are scriptable
- **WHEN** an operator requests JSON output for effective scopes
- **THEN** the command emits machine-readable user, group path, and scope data
  without password material
