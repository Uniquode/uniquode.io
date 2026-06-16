## MODIFIED Requirements

### Requirement: Modules load settings through settings classes
Modules with runtime configuration SHALL expose a settings class that carries its module configuration definition and loads values through the shared settings loading path.

#### Scenario: Module setup loads runtime settings
- **WHEN** a module needs runtime settings during setup
- **THEN** it loads those settings through its settings class
- **AND** it does not duplicate configuration parsing with an ad hoc config-to-settings helper

#### Scenario: Configuration values require transformation
- **WHEN** configuration values come from TOML, environment, mapping sources, or tests
- **THEN** declared field transforms are applied consistently through the shared settings loading path

#### Scenario: Module is absent
- **WHEN** a module is not configured
- **THEN** settings loading does not invent fallback runtime behaviour for that absent module
