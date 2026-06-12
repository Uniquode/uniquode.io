## ADDED Requirements

### Requirement: Site provides typed settings access
The `Site` object SHALL provide a public way to obtain typed settings or settings-backed capabilities owned by configured modules.

#### Scenario: App requests app-usable module settings
- **WHEN** a host app needs a documented setting owned by a configured module
- **THEN** it obtains that setting through `Site` or a module-owned public capability
- **AND** the returned object is the owning module's public typed settings or protocol

#### Scenario: Settings owner is explicit
- **WHEN** a caller requests typed settings through `Site`
- **THEN** the request identifies the settings owner
- **AND** the owner identifier is not treated as a raw config section name

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
