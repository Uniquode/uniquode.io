## Context

Wevra currently has reusable static settings helpers and application-owned settings objects. Host applications and project commands resolve an application config boundary, load environment values, and construct settings directly. This works for static startup, but it creates direct coupling between consumers and configuration resolution details.

The new model introduces a central configuration service. The host app or CLI remains responsible for deciding which configuration sources exist, such as a specific filename or environment mapping. The service is responsible for source lifecycle, readiness, immutable current config state, and filtered update delivery.

## Goals / Non-Goals

**Goals:**

- Allow app startup and CLI entrypoints to inject configuration sources explicitly.
- Provide `await config.ready()` so startup can block until required initial configuration exists.
- Provide immutable, versioned current config state.
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

### Public package boundary is `wevra.config`

The configuration service belongs in `wevra.config`. This keeps the service independent of any host application while making the public configuration contracts discoverable from a stable package boundary.

The initial package should expose service contracts and first-party source adapters without requiring host applications to import implementation internals.

Alternative considered: place the service under an existing settings or core module. This was rejected because the new service owns runtime readiness, subscriptions, and source lifecycle rather than only static settings parsing.

### App and CLI entrypoints inject sources

The app or CLI constructs source instances and passes them to the configuration service. For example, a CLI can create a file source from its resolved `APP_CONFIG` argument and an environment source from the current process environment.

This avoids a self-bootstrap problem where TOML would need to be read to discover how TOML should be read. It also keeps application boundary decisions at the existing composition layer.

Alternative considered: configure sources from a `[config.sources]` table in the application config file. This was rejected for initial source discovery because it creates circular configuration. A future source can still read provider-specific settings from already-loaded configuration after readiness.

### Async subscription streams are the primitive listener model

Subscribers consume filtered event streams rather than arbitrary callbacks. A subscription exposes an async iterator or queue of `ConfigEvent` values selected by a `ConfigSelector`.

This keeps backpressure and cancellation explicit, avoids one slow callback blocking service dispatch, and is easier to test. Callback helpers can be added later as convenience wrappers over the stream primitive.

Alternative considered: direct callback registration. This was rejected as the primitive because callback ordering, exception handling, and dispatch blocking are harder to reason about.

### Subscription queues use a simple bounded policy

Each subscription uses its own bounded async queue. Dispatch to a slow subscriber must not indefinitely block unrelated subscribers. If a subscriber queue reaches capacity, the service closes that subscription with an overflow error or diagnostic rather than applying complex backpressure or dropping configuration events silently.

Configuration events are expected to be low volume, so the first implementation should keep the policy simple and avoid configurable queue strategies until a concrete need appears.

Alternative considered: unbounded queues. This was rejected because a stuck subscriber could accumulate memory indefinitely. Alternative considered: drop oldest/newest events. This was rejected because configuration event loss is unsafe unless a consumer explicitly asks for lossy behaviour.

### Subscriptions provide a blocking initial config

Subscription registration is cheap and immediate, but configuration availability is explicit through `initial_config(required=True)`. The default is required because most subscribers need configuration data to initialise safely.

`initial_config()` blocks until the configuration service is ready and can return a coherent matching config. If service readiness fails, it raises the readiness error. If `required=True` and no matching configuration exists after readiness, it raises an actionable configuration error. Callers that can operate without matching configuration can pass `required=False` and receive an empty matching config after readiness.

After `initial_config()` returns, the subscription stream delivers matching events newer than that config version without gaps. Internally, subscription creation must register the subscriber before capturing the config version so updates are not lost between initial state delivery and live event consumption.

Alternative considered: make `subscribe()` block. This was rejected because it hides potentially long waits in object construction or context entry and makes lifecycle management less explicit.

### Selectors use explicit configuration fields

Filtering is expressed with a `ConfigSelector`, using fields such as `section`, `key`, `key_prefix`, `source`, and `event_kind`. The public API avoids the term `path` because it is ambiguous with filesystem paths and URL paths.

The service can also carry source-location metadata for diagnostics, such as file, line, and column, but subscribers select semantic configuration addresses rather than raw file lines.

Alternative considered: a generic `subject` string. This was rejected because it is too vague and would recreate stringly typed routing inside the configuration layer.

### Readiness is initial availability, not perpetual stability

`ready()` completes when all required sources have either produced valid initial data or failed with an error. Required source failure before readiness causes `ready()` to raise. Optional source failure emits diagnostics but does not block readiness.

After readiness, sources may continue to emit changes or diagnostics. Consumers that require a current value should use current config after `ready()` or subscribe before awaiting readiness if they need the initial event stream.

Alternative considered: wait for all sources to finish all work. This was rejected because long-lived sources may never finish.

### Local file readiness uses a safety timeout

Local file-backed configuration should become ready quickly. The first implementation should include a reasonable deadlock-protection timeout for local file readiness, initially five seconds, and raise an actionable configuration error if the file source does not become ready in that time.

The timeout is a safety factor, not a retry or remote-source policy. Future non-local sources can define their own readiness expectations when there is a concrete requirement.

Alternative considered: no timeout. This was rejected because a startup deadlock would be harder to diagnose. Alternative considered: broad configurable timeout strategy. This was rejected for the first implementation because only local file and environment sources are in scope.

### Current config is exposed as plain mappings initially

The first implementation exposes current config values as plain immutable mappings. Typed access helpers can be added later when real consumers demonstrate the shape needed.

This keeps the service focused on lifecycle, delivery, filtering, and versioning rather than prematurely designing a typed configuration object model.

Alternative considered: typed accessor API in the first implementation. This was rejected as premature until migration of real consumers shows stable needs.

### Configuration delivery is separate from configuration application

The configuration service delivers current config and events. It does not decide whether a database pool, authentication policy, SMS provider, or template renderer can be reconfigured live.

Each subscriber owns its application policy. A subscriber can apply the update immediately, mark restart required, reject unsupported runtime changes, or emit its own diagnostics.

Alternative considered: central hot-reload enforcement. This was rejected because reload safety is facility-specific.

## Risks / Trade-offs

- Required source readiness can block startup indefinitely if a source never emits. Mitigation: support source-level timeouts and actionable diagnostics.
- Async subscriptions can leak tasks if callers do not close them. Mitigation: make subscriptions async context managers and cancel their queues on exit.
- Required initial configs can fail late-created optional facilities if they use the default policy accidentally. Mitigation: keep `required=True` as the safe default and require optional facilities to opt into `required=False` explicitly.
- Bounded subscription queues can close a slow subscriber. Mitigation: configuration events are low volume, overflow is explicit, and losing events silently is not allowed.
- Config merging can hide source precedence mistakes. Mitigation: define deterministic source ordering and expose source metadata in diagnostics.
- Consumers may assume delivered changes are automatically applied. Mitigation: document that event delivery and runtime application are separate contracts.
- File source diagnostics may need line numbers for operator usability. Mitigation: include optional source-location metadata while keeping selectors semantic.

## Migration Plan

1. Introduce configuration service interfaces, selectors, events, current config state, and source protocol without changing existing settings loaders.
2. Add environment and file source adapters that wrap current environment/app-config loading behaviour.
3. Adapt the simplest existing configuration consumer first to prove the model while preserving existing direct settings construction during transition.
4. Migrate remaining configuration consumers to the service, keeping host app tests focused on host-owned wiring and Wevra tests focused on shared behaviour.
5. Retain compatibility paths only until all current startup and CLI flows construct configuration through the service.

## Open Questions

- Which existing configuration consumer is simplest to migrate first during implementation?
