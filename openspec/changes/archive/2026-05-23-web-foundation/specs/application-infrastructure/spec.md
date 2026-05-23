## MODIFIED Requirements

### Requirement: Source package layout
The system SHALL use a `src/` package layout with `src/uniquode` as the core importable application package, while allowing feature modules and web resources to live in conventional sibling locations under `src/`.

#### Scenario: Package imports from source layout
- **WHEN** the project is installed or run through `uv`
- **THEN** the `uniquode` package resolves from `src/uniquode`

#### Scenario: Infrastructure modules are separated
- **WHEN** a developer inspects `src/uniquode`
- **THEN** application construction, settings, route registration, models, migrations, and shared infrastructure have explicit package locations or documented module boundaries

#### Scenario: Web resources use global roots
- **WHEN** a developer inspects the source tree
- **THEN** templates and static assets live in conventional global roots under `src/` rather than inside `src/uniquode`

#### Scenario: Feature modules may live beside the core package
- **WHEN** a later capability introduces a feature module such as `site`, `auth`, `api`, or `integrations`
- **THEN** the module may live alongside `src/uniquode` and integrate through the application's route and infrastructure boundaries

### Requirement: Template conventions
The system SHALL define the baseline Jinja2 server-rendered template and static asset locations and provide rendering conventions without introducing product-specific UI before requirements need it.

#### Scenario: Template location is configurable
- **WHEN** a developer inspects the project structure or configuration
- **THEN** the Jinja2 template root is supplied through settings with a default value of `src/templates/`

#### Scenario: Static asset location is configurable
- **WHEN** a developer inspects the project structure or configuration
- **THEN** the static asset root is supplied through settings with a default value of `src/static/`

#### Scenario: Static asset route prefix is configurable
- **WHEN** a developer inspects the project structure or configuration
- **THEN** the static asset route prefix is supplied through settings with a default value of `/static/`

#### Scenario: Rendering conventions are explicit
- **WHEN** a developer inspects the web foundation implementation
- **THEN** there is a documented or code-defined rendering helper or boundary that renders templates by path from the configured template root

#### Scenario: HTML dispatch and static serving are separate concerns
- **WHEN** a developer inspects the web foundation implementation
- **THEN** HTML request dispatch and static asset serving are wired as separate mechanisms with distinct configuration and handling boundaries
