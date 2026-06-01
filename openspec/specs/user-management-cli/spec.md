# user-management-cli Specification

## Purpose
TBD - created by archiving change add-user-manager. Update Purpose after archive.
## Requirements
### Requirement: User manager command
The system SHALL provide an `auth_ext`-owned CLI script named `usermgr` for administrative local-user management.

#### Scenario: Project script exists
- **WHEN** a developer inspects project scripts
- **THEN** `usermgr` is defined as a runnable project command

#### Scenario: Command uses identity foundation
- **WHEN** `usermgr` performs user operations
- **THEN** it uses the configured identity persistence and FastAPI Users/auth-extension identity services rather than duplicating password or user-lifecycle logic

#### Scenario: Command loads generic auth configuration
- **WHEN** an operator supplies `--config path/to/auth.toml`
- **THEN** `usermgr` reads identity configuration from the `[auth]` table in that file
- **AND** relative SQLite database paths are resolved relative to the config file directory

#### Scenario: Command supports database override
- **WHEN** `AUTH_DATABASE_URL` is set
- **THEN** `usermgr` uses that database URL instead of the value from `[auth]`

#### Scenario: Scriptable output is available
- **WHEN** an operator requests JSON or CSV output
- **THEN** `usermgr` emits the requested machine-readable format without password material

### Requirement: User creation
The `usermgr` command SHALL create local users through a controlled administrative path.

#### Scenario: Create standard user
- **WHEN** an operator runs `usermgr create` with a valid email and password input
- **THEN** the command creates a verified local non-admin, non-superuser account

#### Scenario: Create admin
- **WHEN** an operator runs `usermgr create` with the admin option
- **THEN** the command creates a verified local user with admin status

#### Scenario: Create superuser
- **WHEN** an operator runs `usermgr create` with the superuser option
- **THEN** the command creates a verified local user with superuser status

#### Scenario: Create unverified user
- **WHEN** an operator runs `usermgr create` with the unverified option
- **THEN** the command creates a local user that must complete the email-token verification flow

#### Scenario: Create user with profile metadata
- **WHEN** an operator runs `usermgr create` with display-name, preferred-name, or timezone options
- **THEN** the command stores the supplied metadata on the user account

#### Scenario: Create user with expiry
- **WHEN** an operator runs `usermgr create` with an expiry option
- **THEN** the command stores the supplied expiry timestamp on the user account

#### Scenario: Duplicate user is rejected
- **WHEN** an operator attempts to create a user with an email address that already exists
- **THEN** the command fails without creating a duplicate account

#### Scenario: Password can be read from stdin
- **WHEN** an operator runs `usermgr create` with `--password -`
- **THEN** the command reads one password value from stdin and does not prompt for confirmation

### Requirement: Password policy
Local-user password writes SHALL use an injectable `auth_ext` password policy boundary.

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
The `usermgr` command SHALL resolve user command targets predictably.

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
The `usermgr` command SHALL update existing users through explicit field options.

#### Scenario: Update admin status
- **WHEN** an operator runs `usermgr update` with `--admin` or `--no-admin`
- **THEN** the command updates the user's admin state

#### Scenario: Update verification status
- **WHEN** an operator runs `usermgr update` with `--verify` or `--no-verify`
- **THEN** the command updates the user's verification state

#### Scenario: Update superuser status
- **WHEN** an operator runs `usermgr update` with `--superuser` or `--no-superuser`
- **THEN** the command updates the user's superuser state

#### Scenario: Sole superuser cannot be demoted
- **WHEN** an operator attempts to remove the superuser flag from the only superuser account
- **THEN** the command fails without changing that account

#### Scenario: Update profile metadata
- **WHEN** an operator runs `usermgr update` with display-name, preferred-name, or timezone options
- **THEN** the command updates the supplied metadata fields

#### Scenario: Clear profile metadata
- **WHEN** an operator runs `usermgr update` with no-display-name, no-preferred-name, or no-timezone options
- **THEN** the command clears the supplied nullable metadata fields

#### Scenario: Update expiry
- **WHEN** an operator runs `usermgr update` with an expiry option
- **THEN** the command updates the user's expiry timestamp

#### Scenario: Clear expiry
- **WHEN** an operator runs `usermgr update` with a no-expiry option
- **THEN** the command clears the user's expiry timestamp

#### Scenario: Update password
- **WHEN** an operator runs `usermgr update` with password input
- **THEN** the command changes the user's password through the existing identity boundary

### Requirement: User deletion
The `usermgr` command SHALL delete users only through an explicit destructive operation.

#### Scenario: Delete requires confirmation
- **WHEN** an operator runs `usermgr delete` without a force option
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
The `usermgr` command SHALL deactivate users without deleting the account row.

#### Scenario: Deactivate target user
- **WHEN** an operator runs `usermgr deactivate` for an existing user
- **THEN** the command marks the user inactive without removing the user record

#### Scenario: Deactivate rejects superuser
- **WHEN** deactivation is requested for a superuser account
- **THEN** the command fails without changing the account active state

#### Scenario: Inactive users remain excluded
- **WHEN** a deactivated user attempts to authenticate or use an existing browser session
- **THEN** existing identity checks reject or neutralise the inactive account

### Requirement: User listing
The `usermgr` command SHALL list users with filters and ordering suitable for operational inspection.

#### Scenario: List all users
- **WHEN** an operator runs `usermgr list` with no filters
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
The `usermgr` command SHALL support changing a user's password through interactive confirmation.

#### Scenario: Password change prompts for confirmation
- **WHEN** an operator runs the password-change command
- **THEN** the command prompts for the new password and confirmation without echoing the entered value

#### Scenario: Password mismatch is rejected
- **WHEN** password and confirmation values do not match
- **THEN** the command fails without changing the user's password

#### Scenario: Password can be read from stdin
- **WHEN** an operator runs the password-change command with `--password -`
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
The system SHALL defer API-backed `usermgr` operation until administrative API tokens/scopes exist.

#### Scenario: Initial implementation uses local service mode
- **WHEN** the first `usermgr` implementation is delivered
- **THEN** it operates through `auth_ext` configured services and database access rather than requiring an admin API token or host-specific settings object

#### Scenario: Future API mode requires admin scope
- **WHEN** a future API-backed mode is introduced
- **THEN** it requires an authenticated token with explicit administrative privileges or scopes

### Requirement: User manager Click parser
The system SHALL use Click for the `usermgr` command parser while preserving the
existing local operator command interface and management outcomes.

#### Scenario: User manager subcommands remain available
- **WHEN** an operator runs `usermgr create`, `usermgr update`, `usermgr delete`,
  `usermgr deactivate`, `usermgr list`, or `usermgr password`
- **THEN** the command accepts the same command names, positional arguments, and
  option names as before the parser migration

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
  parser migration

