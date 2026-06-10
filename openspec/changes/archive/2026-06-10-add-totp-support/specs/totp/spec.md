## ADDED Requirements

### Requirement: TOTP mode and exposure
The system SHALL operate TOTP using a tri-state deployment mode:
`disabled`, `opt_in`, `required`.

#### Scenario: TOTP disabled hides optional method flows
- **WHEN** `totp_mode` is `disabled`
- **THEN** the system does not expose TOTP enrolment setup, reset, challenge, or listing flows

#### Scenario: TOTP opt-in is available for eligible users
- **WHEN** `totp_mode` is `opt_in` and a user has a verified email address
- **THEN** the system can offer TOTP enrolment when policy indicates.

#### Scenario: TOTP required status is tracked and surfaced
- **WHEN** `totp_mode` is `required` and a user has no active TOTP credential
- **THEN** login and post-email-verification flows surface a setup prompt.

### Requirement: TOTP feature enablement and bypass
The system SHALL expose setup when mode is `opt_in` or `required`, and honour bypass rules.

#### Scenario: Opt-in mode does not block login
- **WHEN** `totp_mode` is `opt_in` and a user has no active credential
- **THEN** login completes on primary credentials and TOTP setup remains optional.

#### Scenario: Required mode prompts, allows skip, and re-prompts
- **WHEN** `totp_mode` is `required` and user has no active credential
- **THEN** the user is prompted to set up TOTP after primary login or email verification,
  with an explicit bypass option.
- **WHEN** setup is bypassed
- **THEN** login proceeds and TOTP setup is presented again on the next login attempt.

#### Scenario: Opt-in requires verified email
- **WHEN** `totp_mode` is `opt_in` or `required` and the email is unverified
- **THEN** setup attempts are rejected until the account email is verified.

### Requirement: Enrolment and confirmation
The system SHALL create TOTP credentials through a pending state that must be confirmed
before activation.

#### Scenario: User starts TOTP enrolment
- **WHEN** an eligible authenticated user starts TOTP enrolment
- **THEN** the system creates a pending credential and returns enrolment data including
  QR code material and fallback textual secret generated from a cryptographically secure
  random source.

#### Scenario: Pending credentials are not sufficient for ceremony
- **WHEN** a user has only a pending TOTP credential
- **THEN** it does not satisfy ceremony requirements requiring active TOTP.

#### Scenario: User confirms pending TOTP
- **WHEN** the user submits a valid TOTP code for the pending credential
- **THEN** the system activates the credential for future ceremony checks.

#### Scenario: Invalid confirmation keeps credential pending
- **WHEN** the user submits an invalid TOTP code for the pending credential
- **THEN** the system keeps the credential pending and returns a validation failure.

### Requirement: Login ceremony integration
The system SHALL adapt login UI and flow to TOTP mode using HTMX.

#### Scenario: Default login has email and password only
- **WHEN** the login page is first loaded
- **THEN** the form contains only email and password fields.

#### Scenario: Login response is adapted by HTMX
- **WHEN** primary auth is validated for a user with active TOTP
- **THEN** the form updates to collect TOTP code in-line before final assertion.

#### Scenario: Required/opt-in setup prompt during login
- **WHEN** primary auth is validated and user has no active TOTP
- **THEN** the form updates to a dismissible setup fragment when mode is `required`
  and mode `opt_in` optionally surfaces the opportunity without blocking login.

#### Scenario: Active TOTP verification completes ceremony
- **WHEN** a challenged user submits a valid TOTP code for an active credential
- **THEN** the system records a TOTP assertion and can complete login if policy requirements are met.

#### Scenario: Invalid TOTP rejects ceremony completion
- **WHEN** a challenged user submits an invalid TOTP code
- **THEN** the system rejects the assertion and does not issue session state.

#### Scenario: Login challenge cannot complete if account is inactive
- **WHEN** a user becomes inactive before TOTP or recovery challenge submission
- **THEN** the ceremony rejects the challenge and does not issue session state.

### Requirement: Replay and time-window policy
The system SHALL enforce configured TOTP step, drift, and replay controls during confirmation
and login verification.

#### Scenario: TOTP outside accepted window fails
- **WHEN** a submitted TOTP code is outside the configured accepted window
- **THEN** the system rejects the code.

#### Scenario: Replayed TOTP code fails
- **WHEN** a submitted code reuses a previously consumed step or verifier according to replay policy
- **THEN** the system rejects the code.

### Requirement: Recovery codes as bypass
The system SHALL generate and consume one-time recovery codes associated with TOTP
credentials. Recovery codes are alternate credentials and SHALL NOT be stored in plaintext.

#### Scenario: Recovery codes are generated at enrolment
- **WHEN** TOTP setup is confirmed
- **THEN** the system shows the generated recovery codes once and stores only one-way
  verifiers for those codes.

#### Scenario: Recovery-code verifiers are not reversible encrypted fields
- **WHEN** recovery-code verifiers are persisted
- **THEN** field names do not use the `crypt_` prefix because verifier values are not
  decryptable secret material.

#### Scenario: Recovery codes bypass missing TOTP during ceremony
- **WHEN** policy permits and the user submits a valid unused recovery code
- **THEN** the ceremony can complete and the code is consumed atomically.

#### Scenario: Recovery codes cannot be reused
- **WHEN** a recovery code is used once
- **THEN** the system marks it consumed and rejects future attempts with that code.

### Requirement: TOTP disablement and reset
The system SHALL support disabling and resetting active TOTP credentials while preserving
recovery semantics.

#### Scenario: User disables active TOTP
- **WHEN** an authenticated user satisfies policy controls
- **THEN** the system disables the active credential and returns to setup prompt state
  according to mode.

#### Scenario: TOTP reset invalidates active credential
- **WHEN** a user or admin resets TOTP
- **THEN** the system invalidates the active credential and requires re-enrolment before
  TOTP can satisfy policy again.

#### Scenario: Disabled TOTP cannot satisfy challenge
- **WHEN** a disabled or reset credential is used during login
- **THEN** the system rejects it as unavailable.

### Requirement: TOTP secret protection
The system SHALL protect TOTP secret material from disclosure outside enrolment and
verification surfaces. Reversible persisted TOTP seed material SHALL be encrypted at rest.

#### Scenario: Plaintext seed is never exposed
- **WHEN** TOTP credential records are returned through API, template context,
  logs, or management listings
- **THEN** plaintext seed material is excluded.

#### Scenario: Persisted seed uses encrypted-at-rest storage
- **WHEN** a TOTP credential is stored
- **THEN** the persisted seed value is encrypted using configured Wevra secret storage
  facilities.
- **AND** the field or column storing that value starts with `crypt_`.

#### Scenario: TOTP uses the shared versioned secret key ring
- **WHEN** TOTP seed material is encrypted or decrypted
- **THEN** the system uses the shared Wevra secret envelope/key-ring mechanism used by
  other `crypt_` fields.
- **AND** the key configuration uses universal Wevra secret names rather than
  provider-specific names.
- **AND** current and legacy key versions are supported.

#### Scenario: Encrypted field names identify decryptable secret material
- **WHEN** a field or column name starts with `crypt_`
- **THEN** the value is encrypted-at-rest secret material and callers must treat it as
  decryptable only inside enrolment or verification paths.
- **WHEN** a field or column stores plaintext or a one-way verifier
- **THEN** its name does not start with `crypt_`.

#### Scenario: Verification requires only operational secret access
- **WHEN** verifying TOTP
- **THEN** the system uses only the verification path necessary to validate the code,
  without broad secret leakage.
