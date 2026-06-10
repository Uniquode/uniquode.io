## 1. Core service contracts

- [ ] 1.1 Define configuration event, event kind, source metadata, source diagnostic, and immutable snapshot types.
- [ ] 1.2 Define `ConfigSelector` with explicit fields for section, key, key prefix, source, and event kind.
- [ ] 1.3 Define the async configuration source protocol for start, stop, required/optional readiness, and event publication.
- [ ] 1.4 Define the subscription interface as an async stream or queue with explicit close semantics.

## 2. Configuration service implementation

- [ ] 2.1 Implement source lifecycle management for app/CLI-injected source instances.
- [ ] 2.2 Implement `ready()` so required source success unblocks startup and required source failure raises an actionable configuration error.
- [ ] 2.3 Implement optional source failure handling so optional diagnostics are emitted without blocking readiness.
- [ ] 2.4 Implement deterministic snapshot resolution and version advancement when source updates change resolved values.
- [ ] 2.5 Implement selector matching and filtered event dispatch for section, key, key prefix, source, and event kind.
- [ ] 2.6 Implement subscription cleanup and dispatch isolation so a closed or slow subscriber does not block unrelated subscribers indefinitely.

## 3. Source adapters

- [ ] 3.1 Implement an environment-backed source adapter that accepts an explicit environment mapping from app startup or CLI code.
- [ ] 3.2 Implement a file-backed source adapter that accepts an explicit resolved filename from app startup or CLI code.
- [ ] 3.3 Emit secret-safe diagnostics for source parse, validation, reload, and operational errors.
- [ ] 3.4 Include optional source-location metadata for file-backed values and diagnostics where available.

## 4. Integration and migration

- [ ] 4.1 Wire app startup to construct and inject file and environment sources without requiring the configuration service to discover its own source configuration.
- [ ] 4.2 Wire project CLI paths to construct and inject configuration sources from their resolved command context.
- [ ] 4.3 Preserve existing explicit settings construction for tests and specialised callers.
- [ ] 4.4 Adapt one internal consumer to use selector-based subscription without forcing unrelated consumers to migrate immediately.

## 5. Validation

- [ ] 5.1 Add tests for readiness success, required source failure, optional source diagnostics, and readiness blocking behaviour.
- [ ] 5.2 Add tests for snapshot immutability, deterministic resolution, and version advancement.
- [ ] 5.3 Add tests for selector filtering by section, key, key prefix, source, and event kind.
- [ ] 5.4 Add tests for environment and file source adapters, including secret-safe diagnostics and source-location metadata.
- [ ] 5.5 Run the full applicable test suite and OpenSpec validation before review.
