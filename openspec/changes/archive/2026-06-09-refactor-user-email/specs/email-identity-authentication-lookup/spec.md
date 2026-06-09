## ADDED Requirements

### Requirement: Login by any owned email address
The system SHALL allow password and password+TOTP sign-in starts using any email
address owned by a local user.

#### Scenario: Password login by non-primary email
- **WHEN** an active user submits valid credentials with a non-primary owned email
  address
- **THEN** the system resolves the local user via `identity_user_email` and continues
  the authentication ceremony

#### Scenario: TOTP challenge starts from any owned email
- **WHEN** an active user submits valid password credentials with any owned email
  and TOTP is enabled for that account or deployment
- **THEN** the system keeps the ceremony open and prompts for the TOTP assertion

#### Scenario: Unknown email does not authenticate
- **WHEN** a login attempt uses an email not associated with any local account
- **THEN** the system rejects authentication before password verification

### Requirement: Provider and passkey flows use shared email principal resolution
The system SHALL resolve user principals from provider email claims through the same
email ownership relation used by password flows.

#### Scenario: Provider callback selects local user by owned email
- **WHEN** an external-provider callback carries a verified email that is owned by a local
  user
- **THEN** the callback flow uses that local user as the ceremony principal

#### Scenario: Provider callback rejects cross-account email claims
- **WHEN** a provider callback carries an email already owned by a different local account
- **THEN** the callback flow does not create or switch ownership and returns a
  deterministic conflict result

#### Scenario: Passkey completion binds to pre-resolved local user
- **WHEN** a user completes a passkey assertion for a challenged login
- **THEN** the assertion applies to the locally resolved user established from the
  same email principal resolution path
