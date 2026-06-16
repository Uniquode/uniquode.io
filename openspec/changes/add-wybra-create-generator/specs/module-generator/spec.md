## ADDED Requirements

### Requirement: Generator model supports future module templates
The `wybra-create` command SHALL be structured so additional generator templates can be added without redesigning the CLI command surface.

#### Scenario: Module generator can be registered
- **WHEN** a new module generator is added to Wybra
- **THEN** it can be exposed as a `wybra-create` subcommand or subcommand template without changing the site generator implementation

#### Scenario: Generator dispatch is testable
- **WHEN** generator dispatch is tested
- **THEN** each generator can be invoked through a stable command handler with explicit input options and output paths

### Requirement: Generated modules use Wybra module boundaries
A generated application module SHALL integrate with Wybra through public module boundaries such as module-owned config definitions, async `setup_site(site)`, route declarations, templates, static assets, and public capabilities/helpers.

#### Scenario: Generated module owns its config
- **WHEN** a module template includes module-specific configuration
- **THEN** the generated module declares its own config definition
- **AND** the host app does not need to aggregate that definition

#### Scenario: Generated module exposes route surfaces
- **WHEN** a module template includes web routes
- **THEN** the generated module exposes those routes through the conventional route declaration surface
- **AND** Wybra startup can discover and register them according to configured module order and route publication config

#### Scenario: Generated module setup is async
- **WHEN** a module template requires setup logic
- **THEN** the generated module uses async `setup_site(site)` rather than sync startup hooks or dual sync/async APIs

### Requirement: CRUD and report templates are optional module templates
Wybra SHALL support an extensible direction for CRUD/data-management and report-oriented module templates without making database-backed management a requirement for every site.

#### Scenario: CRUD template is requested explicitly
- **WHEN** a developer requests a CRUD/data-management module template
- **THEN** generated output includes the module structure needed for data management screens and related reports
- **AND** database requirements are attached to that generated module rather than to all generated sites

#### Scenario: Site generation does not imply CRUD
- **WHEN** a developer generates a site without requesting a CRUD/data-management module
- **THEN** the generated site does not include database-backed management screens or reports
