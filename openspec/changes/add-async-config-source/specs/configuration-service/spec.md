## ADDED Requirements

### Requirement: Injected configuration sources
The system SHALL construct the central configuration service from source instances supplied by app startup or CLI entrypoints.

#### Scenario: App injects file source
- **WHEN** app startup resolves an application config filename
- **THEN** it can construct a file-backed configuration source for that filename and inject it into the configuration service

#### Scenario: CLI injects environment source
- **WHEN** a project CLI command needs environment-backed configuration
- **THEN** it can construct an environment-backed source from its selected environment mapping and inject it into the configuration service

#### Scenario: Service does not self-bootstrap source discovery
- **WHEN** the configuration service starts
- **THEN** it does not need to read an application config file to discover which source should read that same file

### Requirement: Readiness contract
The configuration service SHALL provide an async readiness contract that blocks until required initial configuration data is available.

#### Scenario: Required sources become ready
- **WHEN** every required source emits valid initial configuration data
- **THEN** `ready()` completes successfully

#### Scenario: Required source fails before readiness
- **WHEN** a required source reports an unrecoverable error before initial configuration is available
- **THEN** `ready()` fails with an actionable configuration error

#### Scenario: Optional source fails before readiness
- **WHEN** an optional source reports an error before initial configuration is available
- **THEN** `ready()` can still complete if all required sources are ready and the optional source error is emitted as a diagnostic event

### Requirement: Versioned configuration snapshots
The configuration service SHALL expose immutable snapshots of the latest resolved configuration state.

#### Scenario: Snapshot available after readiness
- **WHEN** `ready()` has completed successfully
- **THEN** callers can retrieve a snapshot containing the latest resolved configuration values

#### Scenario: Snapshot versions advance
- **WHEN** a source update changes resolved configuration
- **THEN** the next snapshot has a newer version than the previous snapshot

#### Scenario: Snapshot metadata identifies sources
- **WHEN** a snapshot contains values from one or more sources
- **THEN** diagnostic metadata can identify the source responsible for a value without exposing secret values

### Requirement: Structured configuration events
The configuration service SHALL emit structured events for configuration changes and diagnostics.

#### Scenario: Section value changes
- **WHEN** a source updates values under a configuration section
- **THEN** the service emits events identifying the section and changed keys

#### Scenario: Key is removed
- **WHEN** a source removes a configuration value
- **THEN** the service emits a removal event identifying the section and key

#### Scenario: Source reports diagnostic
- **WHEN** a source reports a parse error, validation error, reload event, or operational message
- **THEN** the service emits a diagnostic event with source metadata and secret-safe details

### Requirement: Selector-based subscriptions
The configuration service SHALL allow subscribers to receive only matching events using structured selectors.

#### Scenario: Subscribe by section
- **WHEN** a subscriber registers a selector for the `identity` section
- **THEN** it receives matching identity configuration events and does not receive unrelated database events

#### Scenario: Subscribe by key prefix
- **WHEN** a subscriber registers a selector for a key prefix within a section
- **THEN** it receives events for keys under that prefix and does not receive sibling keys outside the prefix

#### Scenario: Subscribe by event kind
- **WHEN** a subscriber registers a selector for diagnostic events
- **THEN** it receives matching diagnostics even when they do not update a configuration value

### Requirement: Async subscription streams
The configuration service SHALL expose async subscription streams as the primitive listener mechanism.

#### Scenario: Subscriber consumes events asynchronously
- **WHEN** a subscriber opens a matching subscription
- **THEN** it can consume matching `ConfigEvent` values from an async iterator or queue

#### Scenario: Subscription can be closed
- **WHEN** a subscriber exits or closes its subscription
- **THEN** the service stops delivering events to that subscription and releases associated resources

#### Scenario: Slow subscriber does not block all dispatch
- **WHEN** one subscriber consumes events slowly
- **THEN** the service prevents that subscriber from indefinitely blocking unrelated subscribers

### Requirement: Delivery does not force hot reload
The configuration service SHALL deliver configuration changes without deciding whether each facility applies those changes at runtime.

#### Scenario: Subscriber handles non-reloadable value
- **WHEN** a subscriber receives a change for a value it cannot safely apply at runtime
- **THEN** the subscriber can reject, defer, or report that a restart is required without the configuration service applying the value on its behalf
