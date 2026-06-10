## 1. Core service contracts

- [ ] 1.0 Create the `wevra.config` package boundary and public exports.
- [ ] 1.1 Define configuration event, event kind, source metadata, source diagnostic, and immutable current config types.
- [ ] 1.2 Define `ConfigSelector` with explicit fields for section, key, key prefix, source, and event kind.
- [ ] 1.3 Define the async configuration source protocol for start, stop, required/optional readiness, and event publication.
- [ ] 1.4 Define the subscription interface as an async stream or queue with explicit close semantics and `initial_config(required=True)`.

## 2. Configuration service implementation

- [ ] 2.1 Implement source lifecycle management for app/CLI-injected source instances.
- [ ] 2.2 Implement `ready()` so required source success unblocks startup and required source failure raises an actionable configuration error.
- [ ] 2.3 Implement optional source failure handling so optional diagnostics are emitted without blocking readiness.
- [ ] 2.4 Implement deterministic config resolution and version advancement when source updates change resolved values.
- [ ] 2.5 Implement selector matching and filtered event dispatch for section, key, key prefix, source, and event kind.
- [ ] 2.6 Implement blocking initial configs so subscribers wait for readiness, receive matching current state, and default to required configuration.
- [ ] 2.7 Implement no-gap handoff from initial config version to live matching events.
- [ ] 2.8 Implement bounded per-subscription queues, overflow diagnostics, cleanup, and dispatch isolation so a closed or slow subscriber does not block unrelated subscribers indefinitely.

## 3. Source adapters

- [ ] 3.1 Implement an environment-backed source adapter that accepts an explicit environment mapping from app startup or CLI code.
- [ ] 3.2 Implement a file-backed source adapter that accepts an explicit resolved filename from app startup or CLI code.
- [ ] 3.3 Add a five-second local file readiness safety timeout that raises an actionable configuration error if file readiness deadlocks.
- [ ] 3.4 Emit secret-safe diagnostics for source parse, validation, reload, and operational errors.
- [ ] 3.5 Include optional source-location metadata for file-backed values and diagnostics where available.

## 4. Integration and migration

- [ ] 4.1 Wire app startup to construct and inject file and environment sources without requiring the configuration service to discover its own source configuration.
- [ ] 4.2 Wire project CLI paths to construct and inject configuration sources from their resolved command context.
- [ ] 4.3 Preserve existing explicit settings construction for tests and specialised callers.
- [ ] 4.4 Identify the simplest existing configuration consumer and migrate it first to prove selector-based subscription.
- [ ] 4.5 Migrate remaining current configuration consumers to the configuration service while preserving host app boundary tests.

## 5. Validation

- [ ] 5.1 Add tests for readiness success, required source failure, optional source diagnostics, and readiness blocking behaviour.
- [ ] 5.2 Add tests for plain-mapping current config immutability, deterministic resolution, and version advancement.
- [ ] 5.3 Add tests for blocking initial configs, default `required=True`, optional empty configs, readiness failure propagation, and no-gap event handoff.
- [ ] 5.4 Add tests for selector filtering by section, key, key prefix, source, and event kind.
- [ ] 5.5 Add tests for bounded queue overflow, explicit subscriber closure, and slow-subscriber dispatch isolation.
- [ ] 5.6 Add tests for environment and file source adapters, including file readiness timeout, secret-safe diagnostics, and source-location metadata.
- [ ] 5.7 Run the full applicable test suite and OpenSpec validation before review.
