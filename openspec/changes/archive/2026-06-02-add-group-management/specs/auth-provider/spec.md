## MODIFIED Requirements

### Requirement: Host-provided subject and scope policy
The `auth_provider` boundary SHALL obtain authenticated subjects and allowed scopes from host-provided interfaces backed by the authorisation group model.

#### Scenario: Subject source is external to provider
- **WHEN** the provider needs the current authenticated subject
- **THEN** it asks a host-provided subject resolver rather than importing an application user model

#### Scenario: Scope source is external to provider
- **WHEN** the provider needs to determine allowed scopes
- **THEN** it asks a host-provided scope policy backed by effective group-scope
  resolution rather than embedding group or flag logic

#### Scenario: Duplicate reachable scopes are folded
- **WHEN** the provider receives allowed scopes for a subject through the
  host-provided scope policy
- **THEN** duplicate scopes reached through multiple groups are represented once
  in the allowed scope set

#### Scenario: Provider does not own group policy
- **WHEN** group membership, nested group membership, or group-scope assignment
  changes
- **THEN** the provider relies on the host-provided scope policy to reflect the
  updated effective scopes instead of storing group policy internally
