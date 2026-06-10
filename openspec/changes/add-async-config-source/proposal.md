## Why

Configuration for authentication, database behaviour, feature flags, and provider integration is currently consumed in a fragmented way, with consumers reading environment state directly and assuming static values. This makes startup readiness, runtime reconfiguration, and module-specific configuration ownership hard to coordinate.

We need a central asynchronous configuration service so Wevra owns configuration readiness, current config state, and change notification semantics, while the host app or CLI explicitly injects where configuration comes from.

## What Changes

- Add a central configuration service that accepts app/CLI-injected configuration sources rather than discovering its own source configuration from the file it is meant to load.
- Define a deterministic readiness contract through `ready()` so startup can block until required initial configuration data is available.
- Define immutable, versioned current config state so consumers can read the latest resolved values without coupling to source mechanics.
- Define a structured event stream for configuration messages, section changes, key changes, reloads, removals, and source diagnostics.
- Define subscription filtering through structured selectors such as section, key, key prefix, source, or event kind.
- Provide first-party source adapters for environment-backed values and file-backed values, constructed explicitly by the app startup path or CLI.
- Require listeners to consume filtered async subscriptions as the primitive notification model.
- Keep runtime application of configuration changes owned by the subscribing facility or module; the configuration service delivers changes but does not force hot reload semantics.

## Capabilities

### New Capabilities

- `configuration-service`: Define the central async configuration service, injected sources, readiness handling, current config state, structured selectors, subscriptions, and update events.

### Modified Capabilities

- `environment-configuration`: Change environment-backed configuration from static direct loading only to a source adapter that can feed the central configuration service while preserving explicit settings construction and existing app config boundary rules.

## Impact

- API/contracts impact: Adds a configuration service contract that should become the authoritative model for configuration readiness, current config state, and change delivery in Wevra.
- App/CLI impact: App startup and project commands must construct and inject configuration sources such as file and environment sources into the configuration service.
- Runtime impact: Enables controlled delivery of configuration changes, including feature flags and provider settings, without forcing every consumer to support hot reload.
- Testing impact: Requires tests for source injection, readiness blocking/failure, config state versioning, selector filtering, subscription delivery, and source diagnostics.
- Migration impact: Existing static settings loaders can be adapted gradually by wrapping their current environment and app-config logic as configuration sources.
