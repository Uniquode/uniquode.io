## 1. Core service contracts

- [x] 1.1 Create the `wevra.config` package boundary and public exports.
- [x] 1.2 Define configuration errors, source metadata, source diagnostics, source location metadata, and immutable current config types.
- [x] 1.3 Define the synchronous configuration source protocol for required/optional source loading.
- [x] 1.4 Define simple config access helpers such as `get_config(section)` returning an immutable mapping or `None`.
- [x] 1.5 Define `ConfigDef`, section definition, fields, defaults, and field-keyed env override mapping types.
- [x] 1.6 Define module config discovery for package-root `module_config: ConfigDef`, including re-export support and side-effect-safe import expectations.

## 2. Configuration service implementation

- [x] 2.1 Implement synchronous source loading for app/CLI-injected source instances.
- [x] 2.2 Implement required source failure handling with actionable configuration errors.
- [x] 2.3 Implement optional source failure handling with retained diagnostics.
- [x] 2.4 Implement deterministic config merging and source-order precedence.
- [x] 2.5 Implement source metadata tracking for loaded values.
- [x] 2.6 Remove async readiness, subscription, listener, and queue mechanics from the first implementation.
- [x] 2.7 Implement definition default application, raw field/default handling, and multi-section definition merging.
- [x] 2.8 Implement bootstrap loading of `[app].modules` and raw `[app].database_url`, then discover module `module_config` definitions.

## 3. Source adapters

- [x] 3.1 Implement an environment-backed source adapter that accepts an explicit environment mapping from app startup or CLI code.
- [x] 3.2 Implement a file-backed source adapter that accepts an explicit resolved filename from app startup or CLI code.
- [x] 3.3 Emit secret-safe diagnostics for source parse, validation, and operational errors.
- [x] 3.4 Include optional source-location metadata for file-backed values and diagnostics where available.
- [x] 3.5 Update the environment source adapter to apply registered definition env overrides centrally.

## 4. Integration and migration

- [x] 4.1 Wire app startup to construct and use file and environment sources without requiring the configuration service to discover its own source configuration.
- [x] 4.2 Wire project CLI paths to construct and use configuration sources from their resolved command context after command parsing.
- [x] 4.3 Preserve existing explicit settings construction for tests and specialised callers.
- [x] 4.4 Identify the simplest existing configuration consumer and migrate it first.
- [x] 4.5 Migrate remaining current configuration consumers to the configuration service while preserving host app boundary tests.

## 5. Validation

- [x] 5.1 Add tests for required source success/failure and optional source diagnostics.
- [x] 5.2 Add tests for plain-mapping current config immutability, deterministic resolution, and source-order precedence.
- [x] 5.3 Add tests for section lookup returning mappings or `None`.
- [x] 5.4 Add tests for environment and file source adapters, including secret-safe diagnostics and source-location metadata.
- [x] 5.6 Add tests for config definitions, defaults, raw field/default handling, multi-section definitions, and field-keyed env override handling.
- [x] 5.5 Run the full applicable test suite and OpenSpec validation before review.
