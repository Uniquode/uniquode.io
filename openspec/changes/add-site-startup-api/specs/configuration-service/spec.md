## ADDED Requirements

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
