## ADDED Requirements

### Requirement: Config definitions are owned by the relevant module or platform component
Reusable config definitions SHALL be declared by the Wevra platform component or configured module that owns the setting. The host app SHALL NOT aggregate Wevra-owned database, auth, static, template, validation, or module settings into an app-level config definition file.

#### Scenario: Module declares owned config definitions
- **WHEN** a configured module owns runtime configuration
- **THEN** the module exposes its own config definition through the Wevra config definition discovery boundary
- **AND** the host app does not duplicate that definition

#### Scenario: Platform declares owned config definitions
- **WHEN** Wevra platform startup owns a configuration value
- **THEN** Wevra declares the config definition itself
- **AND** the host app does not need to define that value for Wevra startup to understand it

#### Scenario: App declares product-specific config only
- **WHEN** the host app has product-specific configuration
- **THEN** it may declare config definitions for those product settings in an app-owned config module such as `app.config`
- **AND** those definitions do not include Wevra-owned module settings

#### Scenario: Settings classes bind to their module config definitions
- **WHEN** an app defines a typed settings object
- **THEN** the settings object is constructed from already-resolved config values
- **AND** the settings class declares the app-owned `ConfigDef`
- **AND** the settings section is inferred when that `ConfigDef` declares exactly one section

#### Scenario: Multi-section settings classes name their section
- **WHEN** a typed settings class is backed by a `ConfigDef` with multiple sections
- **THEN** the settings class declares the specific config section it consumes
- **AND** Wevra rejects ambiguous settings loading when the section is omitted

#### Scenario: Wevra-owned runtime config is not bundled with app config
- **WHEN** Wevra needs runtime/platform values such as deployment environment
- **THEN** those values are declared and loaded by Wevra-owned config
- **AND** app-owned config definitions do not import or re-export Wevra runtime config bundles

### Requirement: Config source selection does not create implicit modules
The configuration service SHALL treat configured modules as explicit input. It MUST NOT add database, auth, web, or other modules because related config fields or environment values are present.

#### Scenario: Environment value without module
- **WHEN** an environment value such as `DATABASE_URL` is present
- **AND** the database module is not configured
- **THEN** the configuration service preserves the value as source data where applicable
- **AND** startup does not register a database capability solely because the value exists

#### Scenario: Module omission remains authoritative
- **WHEN** a module is omitted from the configured module list
- **THEN** that module's settings loader and startup hook do not participate in app startup

### Requirement: Config fields own resolution metadata
Config definitions SHALL declare ordered `ConfigField` values. Each field SHALL own its config name, optional default value, optional environment binding, and optional transform callable. The config service SHALL apply transforms after defaults, config sources, and environment overrides have been resolved. Fields without transforms SHALL preserve the resolved value unchanged.

#### Scenario: Field declares default and environment binding together
- **WHEN** a module declares a configurable field
- **THEN** the field name, default value, environment binding, and transform are declared on the same `ConfigField`
- **AND** `ConfigSection` does not use parallel default or environment mappings

#### Scenario: Field transform normalises environment values
- **WHEN** a field declares a transform
- **AND** the effective value comes from an environment override
- **THEN** the config service passes the environment value to the transform
- **AND** stores the transformed value in the resolved config

#### Scenario: Field without transform preserves source value
- **WHEN** a field does not declare a transform
- **THEN** the config service stores the resolved parsed value unchanged

#### Scenario: Invalid transformed value fails configuration loading
- **WHEN** a transform rejects the resolved value
- **THEN** configuration loading fails with a config error that identifies the section and field
- **AND** module startup code does not need to repeat that parsing error handling
