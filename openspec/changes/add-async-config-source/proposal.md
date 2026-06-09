## Why

Configuration for authentication and database behaviour is currently consumed in a fragmented way, with consumers reading environment state directly and assuming static values. This makes startup and runtime reconfiguration hard to coordinate and ties callers to each other’s resolution details.

We need a central, asynchronous configuration protocol so wevra owns config determination once, exposes readiness and change notifications, and allows consumers to receive only the values they need. This supports operational flexibility, including feature flag and connection updates, without ad hoc polling or manual process restart.

## What Changes

- Define a protocol for config sources in wevra that provides one deterministic startup flow (`ready()`), typed snapshot access, and a structured stream of configuration changes.
- Introduce an explicit listener interface so consumers register interest and receive only relevant updates (for example identity/auth settings versus identity-linking settings).
- Add a first-party environment configuration source that translates environment-derived values into the new canonical config protocol.
- Add a first-party file configuration source that reads configuration from file-backed stores and participates in the same readiness and change-stream contract.
- Define this as a foundational architecture change without implementation code in this proposal-only phase.

## Capabilities

### New Capabilities
- `async-config-sources`: Define a shared async protocol for startup readiness, snapshot access, and runtime config updates.
- `config-listener-protocol`: Define how subsystems register interest and consume only relevant configuration updates.
- `environment-config-source`: Define the environment-backed implementation of the async config-source contract.
- `file-config-source`: Define the file-backed implementation of the async config-source contract.

### Modified Capabilities
- `environment-configuration`: Change from static environment loading only to asynchronous generation and propagation through a central config protocol.

## Impact

- API/contracts impact: Adds a new config-source and listener contract that should become the authoritative model for configuration flow in wevra.
- Runtime impact: Enables dynamic updates (including database-related settings) through a controlled readiness-plus-stream mechanism.
- Testing impact: New tests are required for source adapters, subscription filtering, and update semantics in later implementation phases.
- No app code changes are introduced in this proposal-only scope.
