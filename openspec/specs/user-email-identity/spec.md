# user-email-identity Specification

## Purpose
TBD - created by archiving change refactor-user-email. Update Purpose after archive.
## Requirements
### Requirement: Multi-email local user ownership
The system SHALL store email ownership in `identity_user_email` so each local user can
own zero or more verified or unverified addresses.

#### Scenario: User owns multiple email addresses
- **WHEN** the system accepts ownership rows for one local user with distinct emails
- **THEN** all rows are valid and resolve to the same local user when queried through
  the email ownership relation

#### Scenario: User email ownership must include a relation to local account
- **WHEN** an ownership row is created without a valid local user reference
- **THEN** creation is rejected by persistence rules

### Requirement: Global email uniqueness
The system SHALL enforce uniqueness of email addresses across all local accounts.

#### Scenario: Duplicate email addresses are rejected
- **WHEN** two users attempt to claim the same normalized email value
- **THEN** the second claim is rejected and the system reports a unique constraint
  failure

#### Scenario: Case-insensitive duplicates are treated as conflicts
- **WHEN** one user owns `USER@Example.com` and another user attempts to claim
  `user@example.com`
- **THEN** persistence rejects the second claim as duplicate ownership

### Requirement: Primary email is explicit per user
The system SHALL allow one canonical email to be marked as primary for each user.

#### Scenario: First owned email can be marked primary
- **WHEN** a local user creates the first email ownership record
- **THEN** the system marks that email as the primary address unless another
  explicit primary is provided

#### Scenario: Only one email can be primary per user
- **WHEN** two email rows for the same user are marked primary
- **THEN** persistence rejects the second primary claim

