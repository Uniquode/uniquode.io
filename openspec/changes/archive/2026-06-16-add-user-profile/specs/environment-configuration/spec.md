## ADDED Requirements

### Requirement: Media configuration is Wevra-owned
The system SHALL configure media storage through Wevra-owned media configuration rather than app-owned profile configuration.

#### Scenario: Media root is configured
- **WHEN** media configuration provides a media root
- **THEN** Wevra resolves that root relative to the loaded project configuration/root when it is relative
- **AND** media consumers use the resolved media capability rather than resolving paths themselves

#### Scenario: Media serving is configured
- **WHEN** media configuration enables app-served media
- **THEN** Wevra uses the configured media mount path for the media file server

#### Scenario: Media URL mode is configured
- **WHEN** media configuration selects external storage-key URL mode
- **THEN** media URLs are generated from catalogue storage keys for direct static serving
- **AND** profile and widget consumers still request URLs by media ID

#### Scenario: Media configuration is invalid
- **WHEN** media configuration contains an invalid root, mount path, or serving option
- **THEN** configuration or validation fails with a clear media configuration error
