## ADDED Requirements

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
