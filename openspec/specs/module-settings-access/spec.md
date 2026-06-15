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

### Requirement: App does not aggregate Wevra module settings
The host app SHALL NOT expose Wevra-owned module settings as app settings fields. Module-owned settings SHALL be loaded by the owning module from the central configuration service or exposed through a public module capability/helper.

#### Scenario: Auth settings stay module-owned
- **WHEN** auth is configured
- **THEN** auth settings are loaded by the auth module through Wevra config access
- **AND** the host app does not expose auth settings fields solely to bridge auth startup

#### Scenario: Database settings stay module-owned
- **WHEN** database support is configured
- **THEN** database settings are loaded by the database module through Wevra config access
- **AND** the host app does not expose database settings fields solely to bridge database startup

#### Scenario: Wevra tools build module settings without app settings adapters
- **WHEN** Wevra validation or migration tools need database, template, static, or migration settings
- **THEN** they load those values through Wevra-owned project settings and module config definitions
- **AND** the host app does not expose `[tool.wevra]` settings-loader or configuration-error hooks for those tools

#### Scenario: App settings are loaded by Wevra
- **WHEN** the app needs typed product settings
- **THEN** Wevra resolves config file, environment, CLI, and other configured sources through the relevant `ConfigDef`
- **AND** the app does not implement environment loading, project-root discovery, dotenv policy, or config-source precedence itself

#### Scenario: Module settings receive transformed values
- **WHEN** a module setting requires a typed value such as a boolean or path
- **THEN** the owning module declares the field transform on that setting's `ConfigField`
- **AND** its settings loader receives already-transformed values from Wevra config

#### Scenario: Module settings align through their ConfigDef
- **WHEN** a module settings class is loaded
- **THEN** Wevra aligns input values with the settings class's declared `ConfigDef`
- **AND** only fields declared by that `ConfigDef` are passed into the settings object

#### Scenario: Compatible providers are allowed
- **WHEN** a configured module provides the same public capability shape as a Wevra module
- **THEN** app code can depend on the capability shape rather than the concrete Wevra module name
- **AND** startup does not force the Wevra implementation as fallback
