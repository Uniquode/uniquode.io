# auth-management-cli Specification

## Purpose
Define the package-owned administrative authentication management CLI for local
users, groups, scopes, memberships, password operations, and effective-scope
inspection. The current project command is `identitymgr`; a future command
rename to `authmgr` requires a separate behaviour change.
## Requirements
### Requirement: Auth management command
The system SHALL provide a `wevra.auth`-owned CLI script named `wevra-authmgr`
for administrative local identity management, including users, groups, scopes,
memberships, and effective-scope inspection.

#### Scenario: Project script exists
- **WHEN** a developer inspects Wevra package scripts
- **THEN** `wevra-authmgr` is defined as a runnable package command
- **AND** `wevra-identitymgr`, `identitymgr`, and `usermgr` are not defined as
  runnable package commands

#### Scenario: Command uses identity foundation
- **WHEN** `wevra-authmgr` performs user, group, scope, membership, or
  effective-scope operations
- **THEN** it uses the configured identity persistence and FastAPI
  Users/auth-extension identity services rather than duplicating password,
  user-lifecycle, or authorisation-scope logic

#### Scenario: Command loads application auth configuration
- **WHEN** an operator runs `wevra-authmgr` from a resolvable Wevra host
  application project or with `APP_CONFIG` set
- **THEN** `wevra-authmgr` reads identity configuration from the `[auth]` table
  in the resolved application config file
- **AND** it uses the resolved application database URL for identity
  persistence
- **AND** relative SQLite database paths are resolved relative to the
  application config file directory

#### Scenario: Command rejects missing application configuration
- **WHEN** an operator runs `wevra-authmgr` and no application config file can be
  resolved
- **THEN** the command fails with an actionable configuration error that names
  the missing application config boundary
- **AND** the command does not construct auth settings from built-in defaults

#### Scenario: Standalone auth config is not discovered
- **WHEN** `auth.toml` or `AUTH_CONFIG` exists without a resolved application
  config file
- **THEN** `wevra-authmgr` does not use that standalone auth config as the
  command configuration source

#### Scenario: Command supports shared database override
- **WHEN** `DATABASE_URL` is set
- **THEN** `wevra-authmgr` uses `DATABASE_URL` instead of the value from
  `[app].database_url`

#### Scenario: Auth-specific database environment override is ignored
- **WHEN** `AUTH_DATABASE_URL` is set without `DATABASE_URL`
- **THEN** `wevra-authmgr` does not use `AUTH_DATABASE_URL` as the application
  database URL

#### Scenario: Scriptable output is available
- **WHEN** an operator requests JSON or CSV output
- **THEN** `wevra-authmgr` emits the requested machine-readable format without
  password material

#### Scenario: Root command is resource oriented
- **WHEN** an operator runs `wevra-authmgr --help`
- **THEN** the command lists resource command groups for users, groups, and
  scopes
- **AND** top-level user action commands such as `create`, `update`, `delete`,
  `deactivate`, `list`, and `password` are not exposed at the root

### Requirement: User creation
The `wevra-authmgr` command SHALL create local users through a controlled
administrative path.

#### Scenario: Create standard user
- **WHEN** an operator runs `wevra-authmgr user create` with a valid email and password input
- **THEN** the command creates a verified local non-admin, non-superuser account

#### Scenario: Create admin
- **WHEN** an operator runs `wevra-authmgr user create` with the admin option
- **THEN** the command creates a verified local user with admin status

#### Scenario: Create superuser
- **WHEN** an operator runs `wevra-authmgr user create` with the superuser option
- **THEN** the command creates a verified local user with superuser status

#### Scenario: Create unverified user
- **WHEN** an operator runs `wevra-authmgr user create` with the unverified option
- **THEN** the command creates a local user that must complete the email-token verification flow

#### Scenario: Create user with profile metadata
- **WHEN** an operator runs `wevra-authmgr user create` with display-name, preferred-name, or timezone options
- **THEN** the command stores the supplied metadata on the user account

#### Scenario: Create user with expiry
- **WHEN** an operator runs `wevra-authmgr user create` with an expiry option
- **THEN** the command stores the supplied expiry timestamp on the user account

#### Scenario: Duplicate user is rejected
- **WHEN** an operator attempts to create a user with an email address that already exists
- **THEN** the command fails without creating a duplicate account

#### Scenario: Password can be read from stdin
- **WHEN** an operator runs `wevra-authmgr user create` with `--password -`
- **THEN** the command reads one password value from stdin and does not prompt for confirmation

### Requirement: Password policy
Local-user password writes SHALL use an injectable `wevra.auth` password policy boundary.

#### Scenario: Password strength is available
- **WHEN** a caller evaluates a password through the configured password policy
- **THEN** the policy returns a strength score, label, and feedback suitable for a user-facing strength gauge

#### Scenario: Invalid password is rejected
- **WHEN** user creation, password reset, or user-management password change receives a password rejected by the configured policy
- **THEN** the operation fails without storing the password

#### Scenario: Custom policy can be supplied
- **WHEN** a host supplies a custom password policy through identity options
- **THEN** local-user password writes use that policy instead of the default policy

#### Scenario: Default policy settings are configurable
- **WHEN** an operator configures password policy thresholds in `[auth.password.policy]`
- **THEN** the default password policy uses those configured thresholds for local-user password writes

### Requirement: User operational metadata
Local users SHALL store operational metadata needed for user management.

#### Scenario: User timestamps are stored
- **WHEN** a local user is created or updated through the identity boundary
- **THEN** the user stores Unix timestamp float values for creation and modification times
- **AND** the timestamp representation is an explicit requirement, not a
  replaceable implementation detail for this change

#### Scenario: User expiry is stored
- **WHEN** a local user is created or updated with an expiry timestamp
- **THEN** the user stores the expiry as a nullable Unix timestamp float

#### Scenario: Expired users are effectively inactive
- **WHEN** a local user's expiry timestamp is non-null and has passed
- **THEN** identity checks and active-status filtering treat the user as inactive

#### Scenario: Admin flag defaults
- **WHEN** a local user is created without an explicit admin option
- **THEN** the user's admin flag defaults to false

#### Scenario: Last login is tracked
- **WHEN** authentication finalisation succeeds for a local user
- **THEN** the user's last-login timestamp is updated

#### Scenario: Email verification send time is tracked
- **WHEN** a verification email is sent for a local user
- **THEN** the send timestamp is stored so later policy can avoid repeated sends or expire stale unverified accounts

#### Scenario: Preferred timezone defaults
- **WHEN** a local user is created without an explicit preferred timezone
- **THEN** the user stores no preference and runtime presentation falls back to the current server/application timezone

#### Scenario: Display name is optional
- **WHEN** a local user is created without an explicit display name
- **THEN** the user stores no display-name value

#### Scenario: Preferred name is optional
- **WHEN** a local user is created without an explicit preferred name
- **THEN** the user stores no preferred-name value

### Requirement: User target resolution
The `wevra-authmgr` command SHALL resolve user command targets predictably.

#### Scenario: Email target is supplied
- **WHEN** an operator supplies a user target containing `@`
- **THEN** the command validates and resolves the target as an email address

#### Scenario: Identifier target is supplied
- **WHEN** an operator supplies a user target that is not an email address
- **THEN** the command validates and resolves the target as a user ID using the current identity model's ID format

#### Scenario: Malformed target is supplied
- **WHEN** an operator supplies a malformed email target or malformed user ID
- **THEN** the command fails with an invalid-target error instead of reporting the user as missing

### Requirement: User update
The `wevra-authmgr` command SHALL update existing users through explicit field
options.

#### Scenario: Update admin status
- **WHEN** an operator runs `wevra-authmgr user update` with `--admin` or `--no-admin`
- **THEN** the command updates the user's admin state

#### Scenario: Update verification status
- **WHEN** an operator runs `wevra-authmgr user update` with `--verify` or `--no-verify`
- **THEN** the command updates the user's verification state

#### Scenario: Update superuser status
- **WHEN** an operator runs `wevra-authmgr user update` with `--superuser` or `--no-superuser`
- **THEN** the command updates the user's superuser state

#### Scenario: Sole superuser cannot be demoted
- **WHEN** an operator attempts to remove the superuser flag from the only superuser account
- **THEN** the command fails without changing that account

#### Scenario: Update profile metadata
- **WHEN** an operator runs `wevra-authmgr user update` with display-name, preferred-name, or timezone options
- **THEN** the command updates the supplied metadata fields

#### Scenario: Clear profile metadata
- **WHEN** an operator runs `wevra-authmgr user update` with no-display-name, no-preferred-name, or no-timezone options
- **THEN** the command clears the supplied nullable metadata fields

#### Scenario: Update expiry
- **WHEN** an operator runs `wevra-authmgr user update` with an expiry option
- **THEN** the command updates the user's expiry timestamp

#### Scenario: Clear expiry
- **WHEN** an operator runs `wevra-authmgr user update` with a no-expiry option
- **THEN** the command clears the user's expiry timestamp

#### Scenario: Update password
- **WHEN** an operator runs `wevra-authmgr user update` with password input
- **THEN** the command changes the user's password through the existing identity boundary

### Requirement: User deletion
The `wevra-authmgr` command SHALL delete users only through an explicit
destructive operation.

#### Scenario: Delete requires confirmation
- **WHEN** an operator runs `wevra-authmgr user delete` without a force option
- **THEN** the command asks for confirmation before deleting the target user

#### Scenario: Delete removes target user
- **WHEN** deletion is confirmed for an existing user
- **THEN** the command removes that user through the identity persistence boundary

#### Scenario: Delete rejects superuser
- **WHEN** deletion is requested for a superuser account
- **THEN** the command fails without deleting the account

#### Scenario: Missing user delete fails clearly
- **WHEN** an operator attempts to delete a user that does not exist
- **THEN** the command reports that no matching user was found

### Requirement: User deactivation
The `wevra-authmgr` command SHALL deactivate users without deleting the account
row.

#### Scenario: Deactivate target user
- **WHEN** an operator runs `wevra-authmgr user deactivate` for an existing user
- **THEN** the command marks the user inactive without removing the user record

#### Scenario: Deactivate rejects superuser
- **WHEN** deactivation is requested for a superuser account
- **THEN** the command fails without changing the account active state

#### Scenario: Inactive users remain excluded
- **WHEN** a deactivated user attempts to authenticate or use an existing browser session
- **THEN** existing identity checks reject or neutralise the inactive account

### Requirement: User listing
The `wevra-authmgr` command SHALL list users with filters and ordering suitable
for operational inspection.

#### Scenario: List all users
- **WHEN** an operator runs `wevra-authmgr user list` with no filters
- **THEN** the command prints local users in a readable tabular or line-oriented format

#### Scenario: Filter by admin status
- **WHEN** an operator lists users with an admin filter
- **THEN** the command returns only users matching the requested admin status

#### Scenario: Filter by superuser status
- **WHEN** an operator lists users with a superuser filter
- **THEN** the command returns only users matching the requested superuser status

#### Scenario: Filter by email
- **WHEN** an operator lists users with an email or partial-email filter
- **THEN** the command returns only users whose email matches the filter

#### Scenario: Filter by email domain
- **WHEN** an operator lists users with an email-domain filter
- **THEN** the command returns only users whose email domain matches the filter

#### Scenario: Filter by account status
- **WHEN** an operator lists users with `--active`, `--inactive`, `--verified`, or `--unverified`
- **THEN** the command returns only users matching the requested account status

#### Scenario: Filter by timestamp ranges
- **WHEN** an operator lists users with since or before timestamp filters
- **THEN** the command returns only users within the requested created, modified, or last-login range

#### Scenario: Flexible timestamp input is accepted
- **WHEN** an operator supplies timestamp filters or expiry values as Unix timestamps, ISO 8601 variants, or supported natural-language date/time strings
- **THEN** the command parses numeric Unix timestamp values directly and uses `dateparser` for other supported values before applying them as comparable Unix timestamp values
- **AND** digit-only numeric values are treated as Unix seconds rather than
  calendar dates

#### Scenario: Order by supported fields
- **WHEN** an operator requests ordering by email, email domain, creation time, modification time, or last-login time
- **THEN** the command orders by the requested field

#### Scenario: Timestamp range short flags
- **WHEN** an operator uses `-C`, `-c`, `-M`, `-m`, `-L`, or `-l`
- **THEN** the command applies the corresponding since or before timestamp filter

#### Scenario: Wildcards are explicit
- **WHEN** an operator filters email or domain values with `*`
- **THEN** the command treats `*` as the only wildcard and escapes other backend pattern characters

#### Scenario: Human-readable timestamp output
- **WHEN** the command emits human-readable or CSV list output
- **THEN** timestamp fields are rendered as ISO 8601 strings

#### Scenario: JSON omits null fields
- **WHEN** the command emits JSON output for user records
- **THEN** fields with no value are omitted from each user object

### Requirement: Password change
The `wevra-authmgr` command SHALL support changing a user's password through
interactive confirmation.

#### Scenario: Password change prompts for confirmation
- **WHEN** an operator runs `wevra-authmgr user password`
- **THEN** the command prompts for the new password and confirmation without echoing the entered value

#### Scenario: Password mismatch is rejected
- **WHEN** password and confirmation values do not match
- **THEN** the command fails without changing the user's password

#### Scenario: Password can be read from stdin
- **WHEN** an operator runs `wevra-authmgr user password` with `--password -`
- **THEN** the command reads one password value from stdin and does not prompt for confirmation

#### Scenario: Password change updates authentication state
- **WHEN** password change succeeds
- **THEN** the user can authenticate with the new password through the existing identity boundary

#### Scenario: Password change revokes sessions by default
- **WHEN** password change succeeds without a no-revoke option
- **THEN** existing sessions for that user are revoked

#### Scenario: Password change can preserve sessions
- **WHEN** password change succeeds with a no-revoke option
- **THEN** existing sessions for that user are preserved

### Requirement: API-backed mode deferred
The system SHALL defer API-backed `wevra-authmgr` operation until administrative
API tokens/scopes exist.

#### Scenario: Initial implementation uses local service mode
- **WHEN** the first `wevra-authmgr` implementation is delivered
- **THEN** it operates through `wevra.auth` configured services and database
  access rather than requiring an admin API token or host-specific settings
  object

#### Scenario: Future API mode requires admin scope
- **WHEN** a future API-backed mode is introduced
- **THEN** it requires an authenticated token with explicit administrative privileges or scopes

### Requirement: Auth management Click parser
The system SHALL use Click for the `wevra-authmgr` command parser while exposing
user-management operations through a resource-oriented `user` command group.

#### Scenario: User subcommands are grouped under user
- **WHEN** an operator runs `wevra-authmgr user --help`
- **THEN** the command lists `create`, `update`, `delete`, `deactivate`,
  `list`, and `password` user subcommands
- **AND** those subcommands accept the same user operation arguments, options,
  output formats, and exit statuses as the pre-prefix user commands

#### Scenario: Top-level user action commands are rejected
- **WHEN** an operator runs `wevra-authmgr create`, `wevra-authmgr update`,
  `wevra-authmgr delete`, `wevra-authmgr deactivate`, `wevra-authmgr list`, or
  `wevra-authmgr password`
- **THEN** the command fails with a normal Click unknown-command error instead
  of invoking a user operation

#### Scenario: Help paths are accepted
- **WHEN** an operator runs `wevra-authmgr help`,
  `wevra-authmgr help user create`, or `wevra-authmgr user help create`
- **THEN** the command emits the same help output as the corresponding
  `--help` option without invoking the operation
- **AND** command argument or option values equal to `help` remain ordinary
  command input values

#### Scenario: Password source semantics remain protected
- **WHEN** an operator supplies `--password -`
- **THEN** the command reads exactly one non-empty line from non-interactive
  stdin and rejects interactive stdin or extra trailing input
- **AND** when an operator omits the password source or supplies `--password`
  without a value, the command uses a hidden confirmation prompt
- **AND** direct command-line password values other than `-` or the prompt
  sentinel are rejected

#### Scenario: Auth management outputs remain compatible
- **WHEN** user-management operations succeed or fail
- **THEN** the command preserves the existing human, JSON, and CSV output
  contracts and returns the same success or failure exit status as before the
  command-prefix change

### Requirement: Group management commands
The `wevra-authmgr` command SHALL provide local group and scope management
commands through the application auth configuration and database boundaries.

#### Scenario: Group command tree exists
- **WHEN** an operator runs `wevra-authmgr group --help`
- **THEN** the command lists group create, update, delete, list, show,
  membership, scope, and effective-scope operations

#### Scenario: Scope command tree exists
- **WHEN** an operator runs `wevra-authmgr scope --help`
- **THEN** the command lists scope create, update, delete, and list operations

#### Scenario: Group commands use application auth configuration
- **WHEN** an operator runs a group or scope command from a resolved host
  application project or with `APP_CONFIG` set
- **THEN** the command uses the same effective application auth configuration
  and database resolution as existing user commands

### Requirement: Group target resolution
The `wevra-authmgr` command SHALL resolve group command targets by stable group
ID or unique group abbreviation.

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
The `wevra-authmgr` command SHALL allow operators to create, inspect, update,
list, and delete groups safely.

#### Scenario: Create group
- **WHEN** an operator runs `wevra-authmgr group create <abbrev>` with a
  description and one or more scopes
- **THEN** the command creates a group with a stable ID, immutable abbreviation,
  description, and scope assignments

#### Scenario: Update group description
- **WHEN** an operator runs `wevra-authmgr group <id-or-abbrev> update` with a new
  description
- **THEN** the command updates the group description without changing the group
  abbreviation

#### Scenario: List groups
- **WHEN** an operator runs `wevra-authmgr group list`
- **THEN** the command emits group records in human-readable output by default
  and supports JSON or CSV output when requested

#### Scenario: Show group
- **WHEN** an operator runs `wevra-authmgr group <id-or-abbrev> show`
- **THEN** the command shows the group's ID, abbreviation, description, scopes,
  user memberships, child groups, and parent groups

#### Scenario: Delete group with memberships is rejected
- **WHEN** an operator runs `wevra-authmgr group <id-or-abbrev> delete` for a
  group that has users, child groups, or parent groups
- **THEN** the command fails without deleting the group

### Requirement: Scope lifecycle operations
The `wevra-authmgr` command SHALL allow operators to create, update, and list
scope records with optional descriptive text.

#### Scenario: Create scope
- **WHEN** an operator runs `wevra-authmgr scope create <scope> --description <text>`
- **THEN** the command creates the scope record with the supplied description

#### Scenario: Update scope description
- **WHEN** an operator runs `wevra-authmgr scope update <scope> --description <text>`
- **THEN** the command updates the scope description without changing the scope
  string

#### Scenario: Delete unused scope
- **WHEN** an operator runs `wevra-authmgr scope delete <scope>` for a scope that is not
  assigned to any group
- **THEN** the command removes the scope record

#### Scenario: Delete used scope is rejected
- **WHEN** an operator runs `wevra-authmgr scope delete <scope>` for a scope assigned to
  one or more groups
- **THEN** the command fails without removing the scope record

#### Scenario: List scopes
- **WHEN** an operator runs `wevra-authmgr scope list`
- **THEN** the command emits scope records in human-readable output by default
  and supports JSON or CSV output when requested

### Requirement: Group membership operations
The `wevra-authmgr` command SHALL allow operators to assign and remove user and
nested group membership while preventing duplicates and cycles.

#### Scenario: Add user to group
- **WHEN** an operator runs `wevra-authmgr group <id-or-abbrev> add-user <user-target>`
- **THEN** the command adds the target user to the group

#### Scenario: Remove user from group
- **WHEN** an operator runs `wevra-authmgr group <id-or-abbrev> remove-user <user-target>`
- **THEN** the command removes the target user from the group

#### Scenario: Add child group
- **WHEN** an operator runs `wevra-authmgr group <parent-id-or-abbrev> add-group
  <child-id-or-abbrev>`
- **THEN** the command adds the child group to the parent group when the
  relationship does not create a duplicate or cycle

#### Scenario: Remove child group
- **WHEN** an operator runs `wevra-authmgr group <parent-id-or-abbrev> remove-group
  <child-id-or-abbrev>`
- **THEN** the command removes the child group from the parent group

#### Scenario: Cyclic child group is rejected
- **WHEN** an operator attempts to add a child group that would create a cycle
- **THEN** the command fails without changing group membership

### Requirement: User group membership options
The `wevra-authmgr` command SHALL support group membership while creating or
updating users.

#### Scenario: Create user with groups
- **WHEN** an operator runs `wevra-authmgr user create <email>
  --group <id-or-abbrev>` one or more times
- **THEN** the command creates the user and assigns the user to the supplied
  groups

#### Scenario: Add group to user
- **WHEN** an operator runs `wevra-authmgr user update <user-target>
  --add-group <id-or-abbrev>`
- **THEN** the command adds the user to that group without replacing other group
  memberships

#### Scenario: Remove group from user
- **WHEN** an operator runs `wevra-authmgr user update <user-target>
  --rm-group <id-or-abbrev>`
- **THEN** the command removes the user from that group without changing other
  group memberships

#### Scenario: Set user groups
- **WHEN** an operator runs `wevra-authmgr user update <user-target>
  --set-group <id-or-abbrev>` one or more times
- **THEN** the command replaces the user's direct group memberships with exactly
  the supplied groups

#### Scenario: Group replacement is explicit
- **WHEN** an operator runs `wevra-authmgr user update <user-target>
  --group <id-or-abbrev>`
- **THEN** the command rejects the option because replacement uses `--set-group`
  and incremental updates use `--add-group` or `--rm-group`

### Requirement: Effective scope inspection
The `wevra-authmgr` command SHALL allow operators to inspect effective scopes
for a user target.

#### Scenario: Show effective scopes
- **WHEN** an operator runs `wevra-authmgr group effective-scopes <user-target>`
- **THEN** the command prints the de-duplicated scopes resolved through direct
  and nested group membership

#### Scenario: Effective scopes are scriptable
- **WHEN** an operator requests JSON output for effective scopes
- **THEN** the command emits machine-readable user, group path, and scope data
  without password material
