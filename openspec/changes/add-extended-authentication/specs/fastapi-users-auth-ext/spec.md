## MODIFIED Requirements

### Requirement: Storage-portable addon core
The addon SHALL define async storage protocols for external-provider identities
and ceremony-linked challenge metadata rather than coupling the core package to a
specific ORM or database.

#### Scenario: Linked-provider store is protocol-based
- **WHEN** the addon persists linked provider identities and callback state
- **THEN** the core package depends on protocol interfaces rather than the
  application ORM type directly

#### Scenario: Optional storage adapters are supported
- **WHEN** a concrete storage backend is required
- **THEN** optional adapters (for example SQLAlchemy, Beanie, Tortoise, Redis)
  can be attached without changing the addon contracts

### Requirement: Shared ownership of storage contracts
The addon SHALL provide protocol types in `wevra` so applications consume the
link and assertion contracts without adding new schema ownership or provider
persistence tables themselves.

#### Scenario: Host application uses shared contracts
- **WHEN** a host application needs provider-linking persistence and assertion
  flows
- **THEN** the application uses the shared wevra contracts and does not define
  its own provider identity table schema in this change

### Requirement: Provider-identity contracts
The addon SHALL define clear protocol types and errors for provider identity
lookup, linking, unlinking, and callback assertion persistence.

#### Scenario: Provider identity link is stored and resolved
- **WHEN** a valid provider link is created for an authenticated local user
- **THEN** the addon stores provider name and subject and can resolve the same
  link to that local user

#### Scenario: Provider identity callbacks are represented as assertions
- **WHEN** a provider callback returns a verifiable assertion
- **THEN** the addon converts it into a ceremony assertion rather than writing
  session state directly

#### Scenario: Link collisions are surfaced as branchable results
- **WHEN** provider identity linkage is attempted for an already linked subject
- **THEN** the addon returns a branchable conflict result instead of silently
  reassigning ownership

### Requirement: Shared ceremony bridge
The addon SHALL bridge provider-linked assertions into the host ceremony surface
consistently with existing inactive-account and session policies.

#### Scenario: Provider-linked users are ineligible when inactive
- **WHEN** local account checks fail for inactivity or effective expiry
- **THEN** the addon rejects completion and emits a branchable inactive result

#### Scenario: Provider assertion does not bypass final ceremony policy
- **WHEN** a provider assertion succeeds but configured policy requires a
  further assertion
- **THEN** the addon keeps the ceremony incomplete until policy is satisfied
