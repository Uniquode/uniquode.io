## MODIFIED Requirements

### Requirement: Shared ceremony bridge
The addon SHALL bridge provider-linked assertions into the host ceremony surface
consistently with existing inactive-account and session policies, resolving local
user principals through the shared email ownership relation before assertion
finalisation.

#### Scenario: Provider-linked users are ineligible when inactive
- **WHEN** local account checks fail for inactivity or effective expiry after email
  resolution
- **THEN** the addon rejects completion and emits a branchable inactive result

#### Scenario: Provider assertion does not bypass final ceremony policy
- **WHEN** a provider assertion succeeds but configured policy requires a further
  assertion
- **THEN** the addon keeps the ceremony incomplete until policy is satisfied

#### Scenario: Ceremony principal is resolved before provider completion
- **WHEN** a provider callback includes an email claim that maps to a local user
  via `identity_user_email`
- **THEN** the addon resolves that user first and applies the callback to the same
  user context
