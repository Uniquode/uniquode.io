## Context

Wevra currently has reusable static settings helpers and application-owned settings objects. Host applications and project commands resolve an application config boundary, load environment values, and construct settings directly. This works for static startup, but it creates direct coupling between consumers and configuration resolution details.

The new model introduces a central configuration service. The host app or CLI remains responsible for deciding which configuration sources exist, such as a specific filename or environment mapping. The service is responsible for source lifecycle, readiness, immutable snapshots, and filtered update delivery.

## Goals / Non-Goals

**Goals:**

- Allow app startup and CLI entrypoints to inject configuration sources explicitly.
- Provide `await config.ready()` so startup can block until required initial configuration exists.
- Provide immutable, versioned snapshots of resolved configuration.
- Provide filtered async subscriptions so modules receive only relevant configuration events.
- Support environment and file-backed sources without requiring the config service to read TOML in order to discover how to read TOML.
- Keep runtime application policy inside each subscribing module.

**Non-Goals:**

- Do not replace all current settings classes in one step.
- Do not require every setting to become hot-reloadable.
- Do not define provider/vendor-specific config schemas in this change.
- Do not expose physical file line subscriptions as the primary public API.
- Do not introduce a remote configuration service or external dependency.

## Decisions

### App and CLI entrypoints inject sources

The app or CLI constructs source instances and passes them to the configuration service. For example, a CLI can create a file source from its resolved `APP_CONFIG` argument and an environment source from the current process environment.

This avoids a self-bootstrap problem where TOML would need to be read to discover how TOML should be read. It also keeps application boundary decisions at the existing composition layer.

Alternative considered: configure sources from a `[config.sources]` table in the application config file. This was rejected for initial source discovery because it creates circular configuration. A future source can still read provider-specific settings from already-loaded configuration after readiness.

### Async subscription streams are the primitive listener model

Subscribers consume filtered event streams rather than arbitrary callbacks. A subscription exposes an async iterator or queue of `ConfigEvent` values selected by a `ConfigSelector`.

This keeps backpressure and cancellation explicit, avoids one slow callback blocking service dispatch, and is easier to test. Callback helpers can be added later as convenience wrappers over the stream primitive.

Alternative considered: direct callback registration. This was rejected as the primitive because callback ordering, exception handling, and dispatch blocking are harder to reason about.

### Selectors use explicit configuration fields

Filtering is expressed with a `ConfigSelector`, using fields such as `section`, `key`, `key_prefix`, `source`, and `event_kind`. The public API avoids the term `path` because it is ambiguous with filesystem paths and URL paths.

The service can also carry source-location metadata for diagnostics, such as file, line, and column, but subscribers select semantic configuration addresses rather than raw file lines.

Alternative considered: a generic `subject` string. This was rejected because it is too vague and would recreate stringly typed routing inside the configuration layer.

### Readiness is initial availability, not perpetual stability

`ready()` completes when all required sources have either produced valid initial data or failed with an error. Required source failure before readiness causes `ready()` to raise. Optional source failure emits diagnostics but does not block readiness.

After readiness, sources may continue to emit changes or diagnostics. Consumers that require a current value should use snapshots after `ready()` or subscribe before awaiting readiness if they need the initial event stream.

Alternative considered: wait for all sources to finish all work. This was rejected because long-lived sources may never finish.

### Configuration delivery is separate from configuration application

The configuration service delivers snapshots and events. It does not decide whether a database pool, authentication policy, SMS provider, or template renderer can be reconfigured live.

Each subscriber owns its application policy. A subscriber can apply the update immediately, mark restart required, reject unsupported runtime changes, or emit its own diagnostics.

Alternative considered: central hot-reload enforcement. This was rejected because reload safety is facility-specific.

## Risks / Trade-offs

- Required source readiness can block startup indefinitely if a source never emits. Mitigation: support source-level timeouts and actionable diagnostics.
- Async subscriptions can leak tasks if callers do not close them. Mitigation: make subscriptions async context managers and cancel their queues on exit.
- Snapshot merging can hide source precedence mistakes. Mitigation: define deterministic source ordering and expose source metadata in diagnostics.
- Consumers may assume delivered changes are automatically applied. Mitigation: document that event delivery and runtime application are separate contracts.
- File source diagnostics may need line numbers for operator usability. Mitigation: include optional source-location metadata while keeping selectors semantic.

## Migration Plan

1. Introduce configuration service interfaces, selectors, events, snapshots, and source protocol without changing existing settings loaders.
2. Add environment and file source adapters that wrap current environment/app-config loading behaviour.
3. Adapt a small internal consumer to subscribe through the new service while preserving existing direct settings construction.
4. Move additional facilities to subscription-based configuration as requirements arise.
5. Retain compatibility paths until all startup and CLI flows construct configuration through the service.

## Open Questions

- What default readiness timeout should app startup and CLI tools use, if any?
- Should snapshot values be exposed as plain mappings only, or should typed accessors be part of the first implementation?
- Which initial consumers should migrate first after the service contract exists?
