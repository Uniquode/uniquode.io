## MODIFIED Requirements

### Requirement: User manager command
The system SHALL provide an `auth_ext`-owned CLI script named `identitymgr` for
administrative local identity management, including users, groups, scopes,
memberships, and effective-scope inspection.

#### Scenario: Project script exists
- **WHEN** a developer inspects project scripts
- **THEN** `identitymgr` is defined as a runnable project command
- **AND** `usermgr` is not defined as a project command

#### Scenario: Command uses identity foundation
- **WHEN** `identitymgr` performs user, group, scope, membership, or
  effective-scope operations
- **THEN** it uses the configured identity persistence and FastAPI
  Users/auth-extension identity services rather than duplicating password,
  user-lifecycle, or authorisation-scope logic

#### Scenario: Command loads generic auth configuration
- **WHEN** an operator supplies `--config path/to/auth.toml`
- **THEN** `identitymgr` reads identity configuration from the `[auth]` table in
  that file
- **AND** relative SQLite database paths are resolved relative to the config file
  directory

#### Scenario: Command supports database override
- **WHEN** `AUTH_DATABASE_URL` is set
- **THEN** `identitymgr` uses that database URL instead of the value from
  `[auth]`

#### Scenario: Scriptable output is available
- **WHEN** an operator requests JSON or CSV output
- **THEN** `identitymgr` emits the requested machine-readable format without
  password material

#### Scenario: Root command is resource oriented
- **WHEN** an operator runs `identitymgr --help`
- **THEN** the command lists resource command groups for users, groups, and
  scopes
- **AND** top-level user action commands such as `create`, `update`, `delete`,
  `deactivate`, `list`, and `password` are not exposed at the root

### Requirement: User creation
The `identitymgr` command SHALL create local users through a controlled
administrative path.

#### Scenario: Create standard user
- **WHEN** an operator runs `identitymgr user create` with a valid email and
  password input
- **THEN** the command creates a verified local non-admin, non-superuser account

#### Scenario: Create admin
- **WHEN** an operator runs `identitymgr user create` with the admin option
- **THEN** the command creates a verified local user with admin status

#### Scenario: Create superuser
- **WHEN** an operator runs `identitymgr user create` with the superuser option
- **THEN** the command creates a verified local user with superuser status

#### Scenario: Create unverified user
- **WHEN** an operator runs `identitymgr user create` with the unverified option
- **THEN** the command creates a local user that must complete the email-token
  verification flow

#### Scenario: Create user with profile metadata
- **WHEN** an operator runs `identitymgr user create` with display-name,
  preferred-name, or timezone options
- **THEN** the command stores the supplied metadata on the user account

#### Scenario: Create user with expiry
- **WHEN** an operator runs `identitymgr user create` with an expiry option
- **THEN** the command stores the supplied expiry timestamp on the user account

#### Scenario: Duplicate user is rejected
- **WHEN** an operator attempts to create a user with an email address that
  already exists
- **THEN** the command fails without creating a duplicate account

#### Scenario: Password can be read from stdin
- **WHEN** an operator runs `identitymgr user create` with `--password -`
- **THEN** the command reads one password value from stdin and does not prompt
  for confirmation

### Requirement: User update
The `identitymgr` command SHALL update existing users through explicit field
options.

#### Scenario: Update admin status
- **WHEN** an operator runs `identitymgr user update` with `--admin` or
  `--no-admin`
- **THEN** the command updates the user's admin state

#### Scenario: Update verification status
- **WHEN** an operator runs `identitymgr user update` with `--verify` or
  `--no-verify`
- **THEN** the command updates the user's verification state

#### Scenario: Update superuser status
- **WHEN** an operator runs `identitymgr user update` with `--superuser` or
  `--no-superuser`
- **THEN** the command updates the user's superuser state

#### Scenario: Sole superuser cannot be demoted
- **WHEN** an operator attempts to remove the superuser flag from the only
  superuser account
- **THEN** the command fails without changing that account

#### Scenario: Update profile metadata
- **WHEN** an operator runs `identitymgr user update` with display-name,
  preferred-name, or timezone options
- **THEN** the command updates the supplied metadata fields

#### Scenario: Clear profile metadata
- **WHEN** an operator runs `identitymgr user update` with no-display-name,
  no-preferred-name, or no-timezone options
- **THEN** the command clears the supplied nullable metadata fields

#### Scenario: Update expiry
- **WHEN** an operator runs `identitymgr user update` with an expiry option
- **THEN** the command updates the user's expiry timestamp

#### Scenario: Clear expiry
- **WHEN** an operator runs `identitymgr user update` with a no-expiry option
- **THEN** the command clears the user's expiry timestamp

#### Scenario: Update password
- **WHEN** an operator runs `identitymgr user update` with password input
- **THEN** the command changes the user's password through the existing identity
  boundary

### Requirement: User deletion
The `identitymgr` command SHALL delete users only through an explicit
destructive operation.

#### Scenario: Delete requires confirmation
- **WHEN** an operator runs `identitymgr user delete` without a force option
- **THEN** the command asks for confirmation before deleting the target user

#### Scenario: Delete removes target user
- **WHEN** deletion is confirmed for an existing user
- **THEN** the command removes that user through the identity persistence
  boundary

#### Scenario: Delete rejects superuser
- **WHEN** deletion is requested for a superuser account
- **THEN** the command fails without deleting the account

#### Scenario: Missing user delete fails clearly
- **WHEN** an operator attempts to delete a user that does not exist
- **THEN** the command reports that no matching user was found

### Requirement: User deactivation
The `identitymgr` command SHALL deactivate users without deleting the account
row.

#### Scenario: Deactivate target user
- **WHEN** an operator runs `identitymgr user deactivate` for an existing user
- **THEN** the command marks the user inactive without removing the user record

#### Scenario: Deactivate rejects superuser
- **WHEN** deactivation is requested for a superuser account
- **THEN** the command fails without changing the account active state

#### Scenario: Inactive users remain excluded
- **WHEN** a deactivated user attempts to authenticate or use an existing
  browser session
- **THEN** existing identity checks reject or neutralise the inactive account

### Requirement: User listing
The `identitymgr` command SHALL list users with filters and ordering suitable
for operational inspection.

#### Scenario: List all users
- **WHEN** an operator runs `identitymgr user list` with no filters
- **THEN** the command prints local users in a readable tabular or line-oriented
  format

#### Scenario: Filter by admin status
- **WHEN** an operator lists users with an admin filter
- **THEN** the command returns only users matching the requested admin status

#### Scenario: Filter by superuser status
- **WHEN** an operator lists users with a superuser filter
- **THEN** the command returns only users matching the requested superuser
  status

#### Scenario: Filter by email
- **WHEN** an operator lists users with an email or partial-email filter
- **THEN** the command returns only users whose email matches the filter

#### Scenario: Filter by email domain
- **WHEN** an operator lists users with an email-domain filter
- **THEN** the command returns only users whose email domain matches the filter

#### Scenario: Filter by account status
- **WHEN** an operator lists users with `--active`, `--inactive`, `--verified`,
  or `--unverified`
- **THEN** the command returns only users matching the requested account status

#### Scenario: Filter by timestamp ranges
- **WHEN** an operator lists users with since or before timestamp filters
- **THEN** the command returns only users within the requested created,
  modified, or last-login range

#### Scenario: Flexible timestamp input is accepted
- **WHEN** an operator supplies timestamp filters or expiry values as Unix
  timestamps, ISO 8601 variants, or supported natural-language date/time
  strings
- **THEN** the command parses numeric Unix timestamp values directly and uses
  `dateparser` for other supported values before applying them as comparable
  Unix timestamp values
- **AND** digit-only numeric values are treated as Unix seconds rather than
  calendar dates

#### Scenario: Order by supported fields
- **WHEN** an operator requests ordering by email, email domain, creation time,
  modification time, or last-login time
- **THEN** the command orders by the requested field

#### Scenario: Timestamp range short flags
- **WHEN** an operator uses `-C`, `-c`, `-M`, `-m`, `-L`, or `-l`
- **THEN** the command applies the corresponding since or before timestamp
  filter

#### Scenario: Wildcards are explicit
- **WHEN** an operator filters email or domain values with `*`
- **THEN** the command treats `*` as the only wildcard and escapes other backend
  pattern characters

#### Scenario: Human-readable timestamp output
- **WHEN** the command emits human-readable or CSV list output
- **THEN** timestamp fields are rendered as ISO 8601 strings

#### Scenario: JSON omits null fields
- **WHEN** the command emits JSON output for user records
- **THEN** fields with no value are omitted from each user object

### Requirement: Password change
The `identitymgr` command SHALL support changing a user's password through
interactive confirmation.

#### Scenario: Password change prompts for confirmation
- **WHEN** an operator runs `identitymgr user password`
- **THEN** the command prompts for the new password and confirmation without
  echoing the entered value

#### Scenario: Password mismatch is rejected
- **WHEN** password and confirmation values do not match
- **THEN** the command fails without changing the user's password

#### Scenario: Password can be read from stdin
- **WHEN** an operator runs `identitymgr user password` with `--password -`
- **THEN** the command reads one password value from stdin and does not prompt
  for confirmation

#### Scenario: Password change updates authentication state
- **WHEN** password change succeeds
- **THEN** the user can authenticate with the new password through the existing
  identity boundary

#### Scenario: Password change revokes sessions by default
- **WHEN** password change succeeds without a no-revoke option
- **THEN** existing sessions for that user are revoked

#### Scenario: Password change can preserve sessions
- **WHEN** password change succeeds with a no-revoke option
- **THEN** existing sessions for that user are preserved

### Requirement: User manager Click parser
The system SHALL use Click for the `identitymgr` command parser while exposing
user-management operations through a resource-oriented `user` command group.

#### Scenario: User manager subcommands are grouped under user
- **WHEN** an operator runs `identitymgr user --help`
- **THEN** the command lists `create`, `update`, `delete`, `deactivate`,
  `list`, and `password` user subcommands
- **AND** those subcommands accept the same user operation arguments, options,
  output formats, and exit statuses as the pre-prefix user commands

#### Scenario: Top-level user action commands are rejected
- **WHEN** an operator runs `identitymgr create`, `identitymgr update`,
  `identitymgr delete`, `identitymgr deactivate`, `identitymgr list`, or
  `identitymgr password`
- **THEN** the command fails with a normal Click unknown-command error instead
  of invoking a user operation

#### Scenario: Help suffix is accepted
- **WHEN** an operator runs `identitymgr help`, `identitymgr user help`, or
  `identitymgr scope help`
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

#### Scenario: User manager outputs remain compatible
- **WHEN** user-management operations succeed or fail
- **THEN** the command preserves the existing human, JSON, and CSV output
  contracts and returns the same success or failure exit status as before the
  command-prefix change

### Requirement: User group membership options
The `identitymgr` command SHALL support group membership while creating or
updating users.

#### Scenario: Create user with groups
- **WHEN** an operator runs `identitymgr user create <email> --group
  <id-or-abbrev>` one or more times
- **THEN** the command creates the user and assigns the user to the supplied
  groups

#### Scenario: Add group to user
- **WHEN** an operator runs `identitymgr user update <user-target> --add-group
  <id-or-abbrev>`
- **THEN** the command adds the user to that group without replacing other group
  memberships

#### Scenario: Remove group from user
- **WHEN** an operator runs `identitymgr user update <user-target> --rm-group
  <id-or-abbrev>`
- **THEN** the command removes the user from that group without changing other
  group memberships

#### Scenario: Set user groups
- **WHEN** an operator runs `identitymgr user update <user-target> --set-group
  <id-or-abbrev>` one or more times
- **THEN** the command replaces the user's direct group memberships with exactly
  the supplied groups

#### Scenario: Group replacement is explicit
- **WHEN** an operator runs `identitymgr user update <user-target> --group
  <id-or-abbrev>`
- **THEN** the command rejects the option because replacement uses `--set-group`
  and incremental updates use `--add-group` or `--rm-group`
