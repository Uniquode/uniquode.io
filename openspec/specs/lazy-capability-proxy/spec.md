# lazy-capability-proxy Specification

## Purpose
TBD - created by archiving change add-user-profile. Update Purpose after archive.
## Requirements
### Requirement: Capability dependencies resolve lazily by default
The system SHALL provide typed lazy capability proxies so modules can depend on capability shapes without eagerly resolving another module during setup.

#### Scenario: Proxy construction does not require target capability
- **WHEN** a module creates a proxy for another capability during setup
- **THEN** proxy creation succeeds without requiring the target capability to already be registered

#### Scenario: Proxy binds on first required use
- **WHEN** code calls a proxy method that requires the target capability
- **THEN** the proxy resolves the real capability from the site
- **AND** caches the resolved capability for subsequent calls

#### Scenario: Required use without capability fails clearly
- **WHEN** code calls a proxy method that requires a capability that is not registered
- **THEN** the call fails with a clear site capability error
- **AND** no fallback implementation is created

### Requirement: Capability proxies expose the capability shape
The system SHALL make lazy proxies implement the same public capability shape expected by their consumers.

#### Scenario: Consumer receives capability proxy
- **WHEN** a consumer receives a typed capability proxy
- **THEN** it can call the public methods defined by the target capability shape
- **AND** it does not need to know whether the target capability is already bound

#### Scenario: Optional behaviour checks availability explicitly
- **WHEN** a consumer needs to decide whether optional behaviour should render or execute
- **THEN** it uses an explicit availability check
- **AND** the availability check does not bind the target capability unless required by the operation

### Requirement: Module ordering defines precedence, not capability availability
The system SHALL treat configured module order as a precedence rule for ordered surfaces rather than a dependency availability rule for capabilities.

#### Scenario: Later module provides dependency
- **WHEN** a module creates a proxy for a capability that is registered by a later configured module
- **THEN** setup does not fail solely because the target capability is not registered yet
- **AND** the proxy can resolve the capability after all relevant modules have registered their capabilities

#### Scenario: Ordered surfaces still use module precedence
- **WHEN** routes, templates, static files, media overrides, or similar ordered surfaces are registered
- **THEN** configured module order continues to determine precedence for those surfaces

