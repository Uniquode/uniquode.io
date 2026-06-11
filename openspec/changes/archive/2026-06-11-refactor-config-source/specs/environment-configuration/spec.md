## ADDED Requirements

### Requirement: Environment source adapter
The system SHALL provide one environment-backed source adapter that can feed environment-derived values into the central configuration service using registered config definition metadata.

#### Scenario: Environment source is constructed explicitly
- **WHEN** app startup or a CLI command has selected an environment mapping
- **THEN** it can construct an environment source from that mapping and inject it into the configuration service

#### Scenario: Environment source emits canonical values
- **WHEN** the environment source loads
- **THEN** it returns parsed configuration values using the same section and key structure used by configuration service mappings

#### Scenario: Definition defines environment override
- **WHEN** a registered config definition maps a field to one environment variable
- **THEN** the environment source applies that environment value as the raw value for the mapped field

#### Scenario: Definition defines environment fallback list
- **WHEN** a registered config definition maps a field to multiple environment variables
- **THEN** the environment source uses the first configured environment variable present in the selected environment mapping

#### Scenario: Existing settings construction remains available
- **WHEN** tests or specialised callers construct settings explicitly without using the configuration service
- **THEN** explicit settings construction remains available without requiring an environment source

### Requirement: File source adapter
The system SHALL provide a file-backed source adapter that reads a file selected by app startup or CLI entrypoints.

#### Scenario: File source receives resolved filename
- **WHEN** app startup or a CLI command resolves the application config file
- **THEN** it passes that filename to the file source constructor before loading the configuration service

#### Scenario: File source reports parse diagnostics
- **WHEN** a file-backed source cannot parse or validate its input
- **THEN** it reports a secret-safe diagnostic with source metadata

#### Scenario: File source can include source location metadata
- **WHEN** a file-backed source can identify where a value or diagnostic came from
- **THEN** it can include file, line, or column metadata
