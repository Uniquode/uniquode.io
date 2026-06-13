## ADDED Requirements

### Requirement: Site provides type-keyed capability access
The `Site` object SHALL provide public type-keyed capabilities that expose typed settings or settings-backed helpers owned by configured modules.

#### Scenario: App requests app-usable module settings
- **WHEN** a host app or module needs a documented setting owned by a configured module
- **THEN** it obtains a public capability from `Site` by capability type
- **AND** the returned object exposes the owning module's public typed settings or protocol

#### Scenario: Capability type is explicit
- **WHEN** a caller requests settings-backed access through `Site`
- **THEN** the request identifies the public capability type
- **AND** the caller does not depend on provider module names or raw config section names

#### Scenario: Settings access preserves immutability
- **WHEN** `Site` returns module-owned settings
- **THEN** callers receive immutable public settings or a safe public protocol
- **AND** callers cannot mutate shared module settings through the returned object

### Requirement: Host app does not aggregate dependency settings
The host app SHALL NOT aggregate Wevra-owned module settings into its own settings object for cross-module use.

#### Scenario: Auth settings stay auth-owned
- **WHEN** auth settings are needed during startup or by host routes
- **THEN** they are loaded and exposed by Wevra auth through the site composition boundary
- **AND** the host app does not copy auth settings fields into host-owned settings

#### Scenario: Database settings stay database-owned
- **WHEN** database settings are needed during startup or by module code
- **THEN** they are loaded and exposed by Wevra database composition through the site boundary
- **AND** the host app does not duplicate database URL interpretation for Wevra modules
