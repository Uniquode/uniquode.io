## ADDED Requirements

### Requirement: Generated code uses public settings and capability boundaries
Generated site and module code SHALL use Wevra public APIs for configuration access, typed capabilities, and module helpers. It MUST NOT reach into Wevra internals or app-aggregate module settings.

#### Scenario: Generated site reads app-owned settings only
- **WHEN** generated site settings are inspected
- **THEN** they contain only app-owned product settings
- **AND** module-owned settings are not copied into the app settings type

#### Scenario: Generated module depends on capability shape
- **WHEN** generated module code needs another module's behaviour
- **THEN** it requests the public capability or helper for that behaviour
- **AND** it does not assume a concrete Wevra module implementation unless that module is explicitly part of the generated template

#### Scenario: Generated config follows module ownership
- **WHEN** generated config includes module-specific sections
- **THEN** those sections are consumed by the owning module through Wevra config services
- **AND** generated app code does not manually bridge them into module runtime objects
