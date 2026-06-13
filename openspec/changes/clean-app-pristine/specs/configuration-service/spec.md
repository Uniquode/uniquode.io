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
- **THEN** it may declare config definitions for those product settings
- **AND** those definitions do not include Wevra-owned module settings

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
