## ADDED Requirements

### Requirement: Extensible wybra-create command
Wybra SHALL provide a `wybra-create` command with subcommand-based dispatch so site generation and future artefact generators share one command surface.

#### Scenario: Site subcommand is available
- **WHEN** a developer runs `wybra-create site --help`
- **THEN** the command describes site generation options
- **AND** it is exposed from the same `wybra-create` command surface used for future generators

#### Scenario: Unknown subcommand fails clearly
- **WHEN** a developer requests an unsupported generator subcommand
- **THEN** the command fails with an actionable message listing or pointing to supported generator types

### Requirement: Site generator creates a minimal Wybra host app
The `wybra-create site` command SHALL generate the minimal host-app source needed to run a Wybra site while leaving Wybra-owned startup, config, environment, route discovery, route registration, static composition, and template composition inside Wybra.

#### Scenario: Generated site files exist
- **WHEN** a developer runs `wybra-create site --name example --title "Example"`
- **THEN** the generated site includes app-owned files for application startup, context, settings, routes, and views
- **AND** it includes generated configuration when requested by the command options

#### Scenario: Generated site uses Wybra startup
- **WHEN** the generated app entry point is inspected
- **THEN** it uses the public Wybra site startup API
- **AND** it does not manually initialise Wybra database, auth, route discovery, static, template, or module runtime state

#### Scenario: Generated site does not include app environment boilerplate
- **WHEN** the generated file set is inspected
- **THEN** it does not include an app-owned environment loader module for Wybra concerns
- **AND** it does not include an app-owned config definition aggregation file for Wybra-owned settings

### Requirement: Site generation is explicit and safe
The site generator SHALL make output location, module inclusion, config generation, and overwrite behaviour explicit.

#### Scenario: Existing files are protected
- **WHEN** generated output would overwrite an existing file
- **THEN** the command fails before modifying that file unless an explicit overwrite/update option is selected

#### Scenario: Optional modules remain optional
- **WHEN** a developer does not request auth, database, or another optional module
- **THEN** generated config does not include that module
- **AND** generated app code does not create fallback setup for that module

#### Scenario: Requested modules are reflected in config
- **WHEN** a developer requests specific modules during site generation
- **THEN** generated config includes those modules in the requested order
- **AND** Wybra startup uses that configured module order at runtime
