## Why

Configuration is needed before substantial FastAPI app construction: modules, routes, static mounts, templates, CSRF, identity, and database setup all depend on config being available at startup. An async subscription-first model adds complexity without clear benefit for the current startup-heavy configuration needs.

We need a simpler central configuration service that consumes app/CLI-injected sources synchronously, exposes loaded configuration through straightforward lookup helpers, and leaves dynamic change subscriptions for a future requirement.

## What Changes

- Replace the async readiness/subscription-first model with a synchronous loaded configuration service.
- Keep app/CLI-injected sources so the service does not read TOML to discover how TOML should be read.
- Define a `ConfigService` or equivalent object that is built from one or more explicit sources and synchronously loads their values.
- Expose simple read helpers such as `get_config(section)` returning a mapping or `None` when the section is not defined.
- Preserve plain mapping config values as the initial representation.
- Add config definition registration so Wevra modules and host apps can define config sections, known fields, raw defaults, and environment overrides.
- Allow one definition to define or extend multiple section headers.
- Provide first-party source adapters for environment-backed values and file-backed values.
- Preserve explicit settings construction for tests and specialised callers.
- Defer dynamic config watching, background tasks, and listener/subscription notification until a concrete runtime reconfiguration requirement exists.

## Capabilities

### New Capabilities

- `configuration-service`: Define a central synchronous configuration service, injected sources, plain mapping access, source diagnostics, and deterministic source precedence.

### Modified Capabilities

- `environment-configuration`: Change environment-backed configuration from direct ad hoc loading only to a source adapter that can feed the central configuration service while preserving explicit settings construction and existing app config boundary rules.

## Impact

- API/contracts impact: Adds a simpler configuration service contract for startup-time config loading and lookup.
- App/CLI impact: App startup and project commands construct explicit configuration sources such as file and environment sources before building settings.
- Runtime impact: No dynamic subscription or background change propagation is introduced in this change.
- Testing impact: Requires tests for source injection, deterministic precedence, section lookup, missing section behaviour, source diagnostics, definition defaults/env overrides, and file/environment adapters.
- Migration impact: Existing static settings loaders can be migrated by reading from the loaded config service while preserving direct settings construction where needed.
