## ADDED Requirements

### Requirement: Wybra configuration namespace
Environment and application configuration SHALL use `[wybra.*]` sections for
package-owned configuration.

#### Scenario: Configuration names package settings
- **WHEN** application or example configuration names package-owned settings
- **THEN** those settings are declared under `[wybra.*]` namespaces
