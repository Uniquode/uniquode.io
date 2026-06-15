## ADDED Requirements

### Requirement: Environment loading is Wevra-owned for generated and basic sites
A generated or basic Wevra site SHALL NOT require host-app environment loader code. Wevra SHALL provide the environment source loading, optional dotenv loading, and typed raw-value parsing needed by the configuration service and Wevra-owned commands.

#### Scenario: Host app has no environment loader module
- **WHEN** a basic Wevra site is generated or cleaned
- **THEN** no app-owned `environment.py` module is required for startup or Wevra CLI commands

#### Scenario: Dotenv support is centralised
- **WHEN** local dotenv loading is required
- **THEN** Wevra loads it through a Wevra-owned environment source
- **AND** host apps do not wrap dotenv loading themselves

#### Scenario: Env parsing remains minimal
- **WHEN** Wevra parses environment-backed values
- **THEN** it exposes only required behaviours such as lookup, presence checks, bool/int coercion, path handling, and secret-safe diagnostics
- **AND** additional environment framework complexity is not exposed to host apps

### Requirement: Envex is not an app-facing requirement
If `envex` remains in use, it SHALL be encapsulated inside Wevra-owned environment/configuration code and SHALL NOT be required as an app-facing integration layer.

#### Scenario: Envex remains internally useful
- **WHEN** Wevra uses `envex` for required dotenv or parsing behaviour
- **THEN** app code imports Wevra environment/config APIs rather than `envex` or app-owned wrappers around `envex`

#### Scenario: Envex behaviour is unnecessary
- **WHEN** Wevra only needs simple environment lookup and coercion that can be provided directly
- **THEN** the implementation may simplify or remove `envex` usage rather than preserving it by default
