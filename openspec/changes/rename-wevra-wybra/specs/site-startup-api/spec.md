## ADDED Requirements

### Requirement: Wybra module startup identifiers
The site startup API SHALL use `wybra.*` module identifiers when configuring,
loading, validating, or reporting package-owned modules.

#### Scenario: Site startup loads package modules
- **WHEN** the application configures package-owned startup modules
- **THEN** module identifiers use the `wybra.*` namespace
