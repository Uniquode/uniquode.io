## Context

Wevra currently has reusable static settings helpers and application-owned settings objects. Host applications and project commands resolve an application config boundary, load environment values, and construct settings directly.

FastAPI app construction needs much of this configuration before lifespan runs: modules, routes, static mounts, template sources, CSRF, identity, and database state are all currently established in or before app factory construction. Because of that, an async readiness/subscription model is not the right first abstraction for current needs.

The revised design introduces a synchronous configuration service. The app or CLI injects explicit sources, the service consumes them synchronously, and callers read plain mapping config by section/key. Dynamic runtime change handling is intentionally deferred.

## Goals / Non-Goals

**Goals:**

- Allow app startup and CLI entrypoints to inject configuration sources explicitly.
- Load configuration synchronously before settings/app construction needs it.
- Provide simple helpers to read config sections and values.
- Allow Wevra modules and host apps to register config definitions for their own sections or existing sections.
- Preserve plain mapping config values.
- Support environment and file-backed sources without requiring the config service to read TOML in order to discover how to read TOML.
- Preserve existing explicit settings construction for tests and specialised callers.

**Non-Goals:**

- Do not introduce async readiness for startup config.
- Do not introduce subscriptions, listeners, background tasks, or dynamic config watching in this change.
- Do not require every setting to become hot-reloadable.
- Do not define provider/vendor-specific config schemas.
- Do not introduce a remote configuration service or external dependency.

## Decisions

### Public package boundary is `wevra.config`

The configuration service belongs in `wevra.config`. This keeps the service independent of any host application while making the public configuration contracts discoverable from a stable package boundary.

The package should expose the service, source contracts, first-party source adapters, config values, and configuration errors without requiring host applications to import implementation internals.

Alternative considered: place the service under an existing settings or core module. This was rejected because the service owns source loading and config access, not only static environment parsing.

### App and CLI entrypoints inject sources

The app or CLI constructs source instances and passes them to the configuration service. A CLI can resolve the project root and config filename from command context, then construct a file source and environment source explicitly.

This avoids a self-bootstrap problem where TOML would need to be read to discover how TOML should be read. It also keeps application boundary decisions at the existing composition layer.

Alternative considered: configure sources from a `[config.sources]` table in the application config file. This was rejected for initial source discovery because it creates circular configuration.

### Loading is synchronous

The configuration service consumes sources synchronously and returns a loaded current config object. This matches the current app factory and CLI needs, where structural configuration must be available before app setup or command execution continues.

Alternative considered: async readiness and subscriptions. This was rejected for the first implementation because most required configuration is startup configuration and introducing async lifecycle management adds complexity without a current runtime reconfiguration requirement.


### Configuration loading discovers module config definitions

Configuration loading starts from the app/CLI-selected source. The loader first reads enough application configuration to resolve `[app].modules` and `[app].database_url`. The module list is then used to import configured module package roots and inspect each module for `module_config: ConfigDef`. Modules may define `module_config` directly in `__init__.py` or, preferably for non-trivial definitions, re-export it from a small config module to keep `__init__.py` concise.

Each discovered `ConfigDef` contributes section definitions, known raw fields, raw defaults, and field-keyed environment overrides. This allows Wevra modules and host app modules to define their own configuration without hard-coding every section into the core config service.

The initial `[app]` bootstrap is intentionally small because it is needed to discover the rest of the configuration model. Post-load settings code still owns database URL normalisation and validation.

Configured module root imports for config discovery must stay lightweight and side-effect safe. Importing a module to read `module_config` must not open database connections, start services, perform network I/O, or construct an app.

Alternative considered: require every config definition to be supplied manually by app startup. This was rejected because configured modules already define the application composition boundary and should be able to declare their own config requirements.

### Config definitions define sections, fields, defaults, and env overrides

Configuration consumers should not need to hard-code all supported config fields in the core service. Instead, Wevra modules and host apps can register `ConfigDef` definitions. An definition can define or extend one or more section headers. Each section definition can declare known fields, raw default values, and field-keyed environment variable overrides.

The model is intentionally section-oriented. For example, an definition can define `sms.provider` or add keys to an existing `auth` section. Environment variable extraction is handled centrally by one environment source/handler using registered definition metadata rather than every module reading env vars directly.

Conceptual shape:

```python
ConfigDef(
    {
        "sms.provider": ConfigSection(
            fields={
                "provider",
                "sender_id",
                "timeout_seconds",
            },
            defaults={"timeout_seconds": 3600},
            env={
                "provider": "SMS_PROVIDER",
                "sender_id": "SMS_SENDER_ID",
            },
        ),
    },
)
```

Raw defaults are applied before source overrides are merged into the final loaded config. Environment overrides are applied through the central environment source according to registered config definitions. Coercion, path resolution, database URL handling, and cross-field policy remain post-load responsibilities of settings/module code.

Alternative considered: let each module parse its own section and env vars. This was rejected because it preserves the fragmented configuration model this change is intended to remove.

### Config access uses plain mappings

Callers read config through simple helpers. For example, `get_config("auth")` returns the loaded `auth` mapping or `None` if the section is absent. More specific helpers can be added when needed, but the first implementation should keep the API small.

Config values are exposed as immutable plain mappings to avoid accidental mutation after load.

Alternative considered: typed accessor API in the first implementation. This was rejected as premature until real consumers demonstrate stable needs.

### Source precedence is deterministic

When multiple sources provide the same section/key, later sources passed to the service override earlier sources. App/CLI composition controls source order explicitly.

Alternative considered: hidden source precedence inside the service. This was rejected because precedence should be visible at the composition boundary.

### Dynamic config is deferred

If runtime config changes become a concrete requirement, the loaded config service can be extended with a watcher task and listener notification model. That definition should be designed when there is a real consumer for dynamic changes.

Alternative considered: implement subscription hooks now. This was rejected as over-delivery for the current startup-driven configuration use case.

## Risks / Trade-offs

- Startup config remains static after service construction. Mitigation: dynamic watching is explicitly deferred until there is a concrete runtime reconfiguration requirement.
- Plain mappings provide less type guidance than typed accessors. Mitigation: registered definitions define known raw fields and defaults while settings classes perform coercion, normalisation, and concrete policy validation.
- Source precedence mistakes can be subtle. Mitigation: source order is explicit and deterministic, and diagnostics can include source metadata.
- Migrating existing consumers can become too broad. Mitigation: migrate the simplest consumer first and keep explicit settings construction available.

## Migration Plan

1. Replace the async service implementation with a synchronous `wevra.config` package.
2. Add config definition types and register Wevra-owned sections/fields/raw defaults/env overrides.
3. Add file and environment source adapters that wrap current app-config and definition-driven environment parsing behaviour.
4. Migrate settings construction to use loaded config where it reduces direct source coupling.
5. Migrate CLI paths to construct sources explicitly and read loaded config synchronously after command parsing.
6. Preserve direct settings construction for tests and specialised callers.

## Open Questions

- Which existing consumer is the smallest useful migration target after the synchronous service exists?
