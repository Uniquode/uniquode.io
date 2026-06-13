## ADDED Requirements

### Requirement: Host app contains only app-owned site code
The host app SHALL contain only app-specific startup, route surfaces, views, context, and product settings. Generic Wevra configuration, environment loading, validation, module setup, database/auth/web setup, route discovery, route registration, static composition, and template composition SHALL be owned by Wevra or by the configured module that owns the concern.

#### Scenario: Basic app has no Wevra environment adapter
- **WHEN** a basic Wevra host app is inspected
- **THEN** it does not require an app-owned `environment.py` or equivalent wrapper to load Wevra configuration
- **AND** Wevra-owned tools load environment/configuration through Wevra-owned sources or explicit configured module definitions

#### Scenario: Basic app has no Wevra config aggregation file
- **WHEN** a basic Wevra host app is inspected
- **THEN** it does not require an app-owned `config_definitions.py` file for Wevra-owned settings
- **AND** reusable configuration definitions are declared by Wevra or the owning module

#### Scenario: App can omit database and auth modules
- **WHEN** app configuration omits `wevra.db` or `wevra.auth`
- **THEN** startup does not register database or auth capabilities for the omitted modules
- **AND** startup does not synthesise fallback database or auth configuration

#### Scenario: App tests cover app ownership only
- **WHEN** app tests inspect startup and settings behaviour
- **THEN** they assert app-owned route, view, context, and product settings outcomes
- **AND** they do not duplicate Wevra-owned config, environment, auth, database, static, or template internals
