## ADDED Requirements

### Requirement: Canonical local user identity
The system SHALL use a local user account as the canonical identity record for
browser, API, password, and external-provider authentication.

#### Scenario: Local account is canonical
- **WHEN** a user authenticates through any supported method
- **THEN** the authenticated subject resolves to a local user account controlled
  by the application

#### Scenario: External identity does not replace local account
- **WHEN** a user authenticates through an external provider
- **THEN** the provider identity is linked to a local account rather than
  becoming the canonical user record

### Requirement: External provider identity model
The system SHALL maintain a normalised provider registry in `wevra` where each
provider identity record stores `provider_name` and `provider_subject` and links to
one local user through a dedicated link record.

#### Scenario: Linked external identities resolve to local users
- **WHEN** a provider callback resolves a previously linked provider identity
- **THEN** the system resolves that identity to the linked local user

#### Scenario: Provider identity uses stable linkage key
- **WHEN** provider identity data is stored
- **THEN** provider name and provider-subject are used as the canonical external
  identity key in a single provider identity row

#### Scenario: Provider identity linkage is deterministic
- **WHEN** a provider callback resolves the same external identity again
- **THEN** the callback resolves to the same linked local account only if the link
  is owned by that account

#### Scenario: Provider identity collisions are deterministic
- **WHEN** a link is attempted against a provider identity already owned by
  another local account
- **THEN** the system rejects the attempt with a conflict and does not reassign
  ownership

#### Scenario: Ownership conflict requires explicit unlink
- **WHEN** an authenticated local user links a provider identity already linked
  to another user
- **THEN** the system requires the prior owner to unlink first and rejects the
  new link attempt

### Requirement: Normalised link model
The system SHALL use two related records:

- `identity_provider` records (provider_name, provider_subject, provider metadata)
- link records binding `user_id` and `provider_id`

#### Scenario: Provider identity and user link are one-to-one at each side
- **WHEN** a provider identity or user-provider pair is linked
- **THEN** the system enforces unique `provider_id` and unique `(user_id, provider_id)`
  pairs in the link table

### Requirement: External account-linkage flows
The system SHALL allow authenticated local users to link and unlink external
provider identities while preserving local account control.

#### Scenario: User links external provider identity
- **WHEN** an authenticated local user starts linking a provider
- **THEN** the system requires an authenticated local context and creates link
  state for that account and provider

#### Scenario: User unlinks external provider identity
- **WHEN** an authenticated local user unlinks a linked provider identity
- **THEN** that identity cannot satisfy authentication assertions for the local
  account afterwards

#### Scenario: Provider identity unlinking respects last usable method policy
- **WHEN** unlinking would remove the final supported login or recovery route
- **THEN** the system rejects unlinking unless explicit policy allows

### Requirement: Provider identities in ceremony flow
The system SHALL represent successful external-provider callback results as
assertions in the authentication ceremony rather than as direct session writes.

#### Scenario: Provider callback can participate in ceremony
- **WHEN** an enabled external-provider callback succeeds against a linked local
  account
- **THEN** the ceremony records a provider assertion and completes only when
  configured policy is satisfied

#### Scenario: Inactive user does not complete by provider callback
- **WHEN** a provider callback resolves to an inactive local account
- **THEN** the ceremony rejects the callback and does not issue browser
  authentication state
