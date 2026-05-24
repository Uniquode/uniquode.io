## ADDED Requirements

### Requirement: User manager command
The system SHALL provide a project CLI script named `usermgr` for administrative local-user management.

#### Scenario: Project script exists
- **WHEN** a developer inspects project scripts
- **THEN** `usermgr` is defined as a runnable project command

#### Scenario: Command uses identity foundation
- **WHEN** `usermgr` performs user operations
- **THEN** it uses the configured identity persistence and FastAPI Users/application identity services rather than duplicating password or user-lifecycle logic

### Requirement: User creation
The `usermgr` command SHALL create local users through a controlled administrative path.

#### Scenario: Create standard user
- **WHEN** an operator runs `usermgr create` with a valid email and password input
- **THEN** the command creates a local non-administrative user account

#### Scenario: Create administrative user
- **WHEN** an operator runs `usermgr create` with the administrative option
- **THEN** the command creates a local user with administrative/superuser status

#### Scenario: Duplicate user is rejected
- **WHEN** an operator attempts to create a user with an email address that already exists
- **THEN** the command fails without creating a duplicate account

### Requirement: User deletion
The `usermgr` command SHALL delete users only through an explicit destructive operation.

#### Scenario: Delete requires confirmation
- **WHEN** an operator runs `usermgr delete` without a force option
- **THEN** the command asks for confirmation before deleting the target user

#### Scenario: Delete removes target user
- **WHEN** deletion is confirmed for an existing user
- **THEN** the command removes that user through the identity persistence boundary

#### Scenario: Missing user delete fails clearly
- **WHEN** an operator attempts to delete a user that does not exist
- **THEN** the command reports that no matching user was found

### Requirement: User listing
The `usermgr` command SHALL list users with filters and ordering suitable for operational inspection.

#### Scenario: List all users
- **WHEN** an operator runs `usermgr list` with no filters
- **THEN** the command prints local users in a readable tabular or line-oriented format

#### Scenario: Filter by admin status
- **WHEN** an operator lists users with an administrative-user filter
- **THEN** the command returns only users matching the requested administrative status

#### Scenario: Filter by email
- **WHEN** an operator lists users with an email or partial-email filter
- **THEN** the command returns only users whose email matches the filter

#### Scenario: Order by supported date fields
- **WHEN** an operator requests ordering by creation date or last-login date
- **THEN** the command orders by the requested field when that field is supported, or fails clearly when it is not yet available

### Requirement: Password change
The `usermgr` command SHALL support changing a user's password through interactive confirmation.

#### Scenario: Password change prompts for confirmation
- **WHEN** an operator runs the password-change command
- **THEN** the command prompts for the new password and confirmation without echoing the entered value

#### Scenario: Password mismatch is rejected
- **WHEN** password and confirmation values do not match
- **THEN** the command fails without changing the user's password

#### Scenario: Password change updates authentication state
- **WHEN** password change succeeds
- **THEN** the user can authenticate with the new password through the existing identity boundary

### Requirement: API-backed mode deferred
The system SHALL defer API-backed `usermgr` operation until administrative API tokens/scopes exist.

#### Scenario: Initial implementation uses local service mode
- **WHEN** the first `usermgr` implementation is delivered
- **THEN** it operates through local configured services and database access rather than requiring an admin API token

#### Scenario: Future API mode requires admin scope
- **WHEN** a future API-backed mode is introduced
- **THEN** it requires an authenticated token with explicit administrative privileges or scopes
