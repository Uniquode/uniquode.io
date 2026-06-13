## ADDED Requirements

### Requirement: App does not aggregate Wevra module settings
The host app SHALL NOT expose Wevra-owned module settings as app settings fields. Module-owned settings SHALL be loaded by the owning module from the central configuration service or exposed through a public module capability/helper.

#### Scenario: Auth settings stay module-owned
- **WHEN** auth is configured
- **THEN** auth settings are loaded by the auth module through Wevra config access
- **AND** the host app does not expose auth settings fields solely to bridge auth startup

#### Scenario: Database settings stay module-owned
- **WHEN** database support is configured
- **THEN** database settings are loaded by the database module through Wevra config access
- **AND** the host app does not expose database settings fields solely to bridge database startup

#### Scenario: Compatible providers are allowed
- **WHEN** a configured module provides the same public capability shape as a Wevra module
- **THEN** app code can depend on the capability shape rather than the concrete Wevra module name
- **AND** startup does not force the Wevra implementation as fallback
