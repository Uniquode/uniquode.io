## ADDED Requirements

### Requirement: Site exposes lazy capability proxies
The system SHALL expose a public site API for obtaining typed lazy capability proxies in addition to immediate capability lookup.

#### Scenario: Module requests capability proxy during setup
- **WHEN** module setup requests a lazy proxy for a capability type
- **THEN** the site returns a proxy without immediately requiring that capability to be registered

#### Scenario: Immediate capability lookup remains available
- **WHEN** startup genuinely requires a capability before continuing
- **THEN** the site can still perform immediate required lookup
- **AND** missing required startup capabilities fail during setup

### Requirement: Startup avoids eager runtime dependency binding
The system SHALL avoid resolving runtime-only cross-module capability dependencies during module setup.

#### Scenario: Runtime dependency is absent during setup
- **WHEN** a configured module depends on another capability only for runtime operations
- **THEN** module setup registers its own capability without requiring the runtime dependency to already exist

#### Scenario: Runtime dependency is missing at use time
- **WHEN** a runtime operation uses a lazy proxy for a capability that is absent
- **THEN** the operation fails with a clear capability error at the operation boundary
