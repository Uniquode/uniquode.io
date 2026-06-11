## MODIFIED Requirements

### Requirement: Environment-backed settings
The system SHALL load application runtime configuration from environment variables through the `envex` module and expose those raw values through the central configuration provider before owner-specific typed settings are built.

#### Scenario: Default settings use environment values
- **WHEN** the application is created without explicit settings
- **THEN** it uses envex-backed environment configuration for supported runtime settings

#### Scenario: Environment names remain concise
- **WHEN** supported application environment variables are documented or validated
- **THEN** conventional names such as `DATABASE_URL` are used directly and app-specific names use concise names such as `APP_ENV`, `APP_RELOAD`, and `CSRF_SECRET`

#### Scenario: Explicit settings remain available
- **WHEN** tests or callers construct host app settings with explicit values
- **THEN** those host-owned values can be used without mutating process environment or constructing dependency-owned settings objects

#### Scenario: Settings loading mechanics are reusable
- **WHEN** an application uses the shared envex and app composition pattern
- **THEN** reusable environment parsing, app configuration loading, central config construction, and settings-provider access are provided by `wevra.core` or `wevra.config`, while concrete typed settings fields and deployment policy remain owned by the module that uses them

#### Scenario: Module settings are not app settings
- **WHEN** a reusable module defines typed settings for its own behaviour
- **THEN** those settings are loaded through the module's settings interface rather than being added to the host app settings object
