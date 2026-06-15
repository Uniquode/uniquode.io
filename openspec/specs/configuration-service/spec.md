# configuration-service Specification

## Purpose
Define the central synchronous configuration service used by app startup, CLI
entrypoints, and configured modules.
## Requirements
### Requirement: Injected configuration sources
The system SHALL construct the configuration service from source instances supplied by app startup or CLI entrypoints.

#### Scenario: App injects file source
- **WHEN** app startup resolves an application config filename
- **THEN** it can construct a file-backed configuration source for that filename and inject it into the configuration service

#### Scenario: CLI injects environment source
- **WHEN** a project CLI command needs environment-backed configuration
- **THEN** it can construct an environment-backed source from its selected environment mapping and inject it into the configuration service

#### Scenario: Service does not self-bootstrap source discovery
- **WHEN** the configuration service loads
- **THEN** it does not need to read an application config file to discover which source should read that same file

### Requirement: Synchronous config loading
The configuration service SHALL load configuration synchronously from its injected sources.

#### Scenario: Sources load successfully
- **WHEN** all required injected sources load successfully
- **THEN** callers can read the loaded current config immediately after service construction or load completion

#### Scenario: Required source fails
- **WHEN** a required source cannot load
- **THEN** configuration loading fails with an actionable configuration error

#### Scenario: Optional source fails
- **WHEN** an optional source cannot load
- **THEN** loading can still succeed if all required sources load and the optional failure is available as a diagnostic

### Requirement: Plain mapping config access
The configuration service SHALL expose loaded configuration as immutable plain mappings.

#### Scenario: Section exists
- **WHEN** `get_config("auth")` is called and the `auth` section is loaded
- **THEN** it returns an immutable mapping for that section

#### Scenario: Section is absent
- **WHEN** `get_config("missing")` is called and no matching section is loaded
- **THEN** it returns `None`

#### Scenario: Loaded config is immutable
- **WHEN** a caller receives a loaded config mapping
- **THEN** mutating that mapping is not allowed

### Requirement: Deterministic source precedence
The configuration service SHALL resolve duplicate keys deterministically based on injected source order.

#### Scenario: Later source overrides earlier source
- **WHEN** two sources provide the same section and key
- **THEN** the value from the later source is present in the loaded config

#### Scenario: Source metadata identifies value origin
- **WHEN** a loaded value came from a source
- **THEN** diagnostic metadata can identify the source responsible for that value without exposing secret values

### Requirement: Module config definition discovery
The configuration loader SHALL discover module config definitions from configured module package roots after resolving the bootstrap application module list.

#### Scenario: Module exposes config definition
- **WHEN** a configured module package root exposes `module_config: ConfigDef`
- **THEN** the loader includes that definition when applying raw defaults and field-keyed environment overrides

#### Scenario: Module re-exports config definition
- **WHEN** a configured module package root re-exports `module_config` from an internal config module
- **THEN** the loader treats it the same as a directly defined package-root value

#### Scenario: Module has no config definition
- **WHEN** a configured module does not expose `module_config`
- **THEN** configuration loading continues without requiring a definition from that module

#### Scenario: Module config discovery is side-effect safe
- **WHEN** the loader imports a configured module package root to inspect `module_config`
- **THEN** that import is expected to avoid database connections, service startup, network I/O, or app construction

#### Scenario: Bootstrap app config identifies modules
- **WHEN** configuration loading starts from an app/CLI-selected source
- **THEN** the loader first resolves `[app].modules` so module config definitions can be discovered

#### Scenario: Bootstrap app config identifies database URL
- **WHEN** configuration loading starts from an app/CLI-selected source
- **THEN** the loader captures raw `[app].database_url` before post-load database URL normalisation occurs

### Requirement: Config definition registration
The configuration service SHALL allow Wevra modules and host applications to register config definitions that define or extend one or more section headers.

#### Scenario: Definition defines a new section
- **WHEN** an definition defines fields for a new section header
- **THEN** the loaded config can include that section after raw default application

#### Scenario: Definition extends an existing section
- **WHEN** an definition defines additional fields for an existing section header
- **THEN** those fields are exposed with the rest of that section's config

#### Scenario: Definition defines multiple sections
- **WHEN** one definition defines more than one section header
- **THEN** each section definition participates in loading, raw defaults, and field-keyed environment overrides

### Requirement: Config fields and raw defaults
The configuration service SHALL use registered definitions to apply raw defaults for registered fields.

#### Scenario: Default value is defined
- **WHEN** a registered field has a default and no source provides a value
- **THEN** the loaded config contains the default value

#### Scenario: Post-load coercion remains external
- **WHEN** a loaded raw value requires coercion, path resolution, URL resolution, or cross-field validation
- **THEN** the consuming settings or module code performs that processing after reading the loaded config

#### Scenario: Unknown field is loaded
- **WHEN** a source provides a field not defined by registered definitions
- **THEN** the field remains available as plain mapping config unless a stricter definition policy is explicitly introduced later

### Requirement: Source diagnostics
The configuration service SHALL collect secret-safe diagnostics from source loading.

#### Scenario: Source reports diagnostic
- **WHEN** a source reports a parse error, validation error, or operational message
- **THEN** the service exposes a diagnostic with source metadata and secret-safe details

### Requirement: Dynamic subscriptions are deferred
The system SHALL NOT introduce runtime subscriptions, listeners, or background config watching in this change.

#### Scenario: Runtime change notification is needed later
- **WHEN** a concrete runtime reconfiguration requirement is introduced
- **THEN** listener or subscription support is designed as a separate change

### Requirement: Startup accepts explicit config source
Wevra site startup SHALL accept configuration sources supplied by the host application or CLI rather than discovering source configuration by reading the same config file first.

#### Scenario: App passes file config source
- **WHEN** a host app or CLI resolves an app config file path
- **THEN** it can pass that path or an equivalent source object to Wevra startup
- **AND** Wevra constructs the central configuration service from that explicit source

#### Scenario: CLI passes config overrides
- **WHEN** CLI arguments represent configuration overrides rather than FastAPI constructor options
- **THEN** those overrides can be passed into Wevra startup as explicit config inputs
- **AND** Wevra applies them through the same central configuration precedence rules as other startup sources

#### Scenario: FastAPI constructor options stay outside config loading
- **WHEN** CLI arguments are needed to construct the FastAPI app itself
- **THEN** the host app applies those values before calling Wevra startup
- **AND** Wevra startup does not retroactively own FastAPI constructor configuration

### Requirement: Startup config drives module composition
The central configuration loaded during Wevra startup SHALL drive configured modules, module config definitions, route configuration, database configuration, and module-owned settings construction.

#### Scenario: Modules are resolved from startup config
- **WHEN** Wevra startup loads the central configuration
- **THEN** it resolves the configured module list from that configuration
- **AND** discovers module config definitions before constructing module-owned typed settings

#### Scenario: Config remains raw until owned by settings
- **WHEN** a module consumes loaded config during startup
- **THEN** the module's settings loader performs coercion, validation, defaults, and policy interpretation
- **AND** host app code does not perform that interpretation for Wevra-owned sections

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
- **AND** `ConfigGroup` does not use parallel default or environment mappings

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
