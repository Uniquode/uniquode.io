# module-settings-access Specification

## Purpose
TBD - created by archiving change refactor-app-settings. Update Purpose after archive.
## Requirements
### Requirement: Module-owned typed settings
The system SHALL let each module define and load its own typed settings from the central raw configuration service.

#### Scenario: Module loads owned settings
- **WHEN** a module needs typed settings for its own runtime behaviour
- **THEN** it loads those settings through a module-owned loader or accessor using the central raw configuration service

#### Scenario: Module validates owned settings
- **WHEN** raw configuration values require coercion, defaults, or policy validation
- **THEN** the owning module applies that interpretation close to where the settings are used

#### Scenario: Module settings are deeply immutable
- **WHEN** a module-owned settings object has been constructed
- **THEN** callers can share it by reference without mutating its public fields or nested public values

#### Scenario: Mutable raw values are normalised by settings loaders
- **WHEN** raw configuration contains mutable values that become part of typed settings
- **THEN** the owning settings loader converts them to immutable public forms before returning the settings object

#### Scenario: Module settings expose owner policy
- **WHEN** a settings-derived policy decision belongs to the owning module
- **THEN** the module settings object may expose that decision through a method on its public settings type

### Requirement: Host app settings boundary
The system SHALL keep the host app settings object focused on host-owned runtime policy and configuration.

#### Scenario: Dependency settings are not aggregated by the host app
- **WHEN** a dependency module such as `wevra.auth` owns typed settings
- **THEN** the host app settings object does not need to expose those settings as its own fields

#### Scenario: Host-owned settings remain explicit
- **WHEN** tests or specialised callers construct host app settings directly
- **THEN** they can provide host-owned values without constructing dependency-owned settings objects

### Requirement: Cross-module settings access
The system SHALL require typed settings owned by another module to be requested through the owning module's settings interface.

#### Scenario: Module requests dependency settings
- **WHEN** one module needs another module's typed settings
- **THEN** it obtains them from the owning module's loader, accessor, or explicit protocol rather than from the host app settings object

#### Scenario: Raw config remains available through the provider
- **WHEN** a module has not yet converted a config section into typed settings
- **THEN** it can still read raw immutable config mappings from the central provider without duplicating another module's typed validation

#### Scenario: Settings owners are distinct from raw config sections
- **WHEN** typed settings are requested across a module boundary
- **THEN** the request uses a settings owner identifier rather than a raw config section header

#### Scenario: Configured modules define the initial owner set
- **WHEN** application startup resolves the configured module list
- **THEN** that module list defines which module settings loaders may participate in startup, without requiring a separate dynamic owner registry

### Requirement: Settings tests follow ownership boundaries
The system SHALL test module-owned settings semantics in the owning module's test suite.

#### Scenario: Dependency settings behaviour is tested in the dependency module
- **WHEN** a setting belongs to a reusable module
- **THEN** coercion, defaults, validation, and policy tests for that setting live with that module rather than in host app tests

#### Scenario: Host app tests cover wiring outcomes
- **WHEN** the host app composes module settings during startup
- **THEN** host app tests assert wiring and integration outcomes without duplicating dependency settings semantics
