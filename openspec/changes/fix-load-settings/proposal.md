## Why

Wevra has a module settings pattern, but not every module consistently uses it.
Some modules still expose ad hoc helpers such as `*_settings_from_config(...)`
that manually read `ConfigService`, parse values, apply defaults, and normalise
types.

That creates several problems:

- settings parsing logic drifts between modules;
- tool settings and runtime settings can validate the same field differently;
- environment-backed values can be transformed differently from file-backed or
  mapping-backed values;
- module setup code becomes inconsistent and harder to reason about;
- review comments keep pointing at duplicated validation helpers rather than
  the actual capability behaviour.

The intended pattern is that each configurable module declares a `ConfigDef`
and exposes a `BaseSettings` subclass. Module setup should call
`Settings.load_settings(site.config)` rather than bespoke config-to-settings
transformers.

## What Changes

- Make `BaseSettings.load_settings(...)` the required runtime settings entry
  point for Wevra modules.
- Audit Wevra modules for ad hoc settings helpers and replace them with
  `BaseSettings` subclasses where configuration is needed.
- Remove or deprecate-in-place internal helpers such as
  `*_settings_from_config(...)` where they only duplicate `load_settings`.
- Keep `ConfigDef`, `ConfigGroup`, and `ConfigField` as the declaration point
  for defaults, environment variable bindings, and transforms.
- Ensure transforms are applied consistently regardless of whether values come
  from TOML, environment, mapping config sources, or tests.
- Improve `BaseSettings.load_settings(...)` if needed so module settings can
  access common composition values such as `project_root` without each module
  inventing its own lookup.
- Keep module settings focused on module-owned configuration. Do not use this
  change to add fallback behaviour for absent modules or absent capabilities.
- Update tests so module setup paths exercise `Settings.load_settings(...)`
  rather than direct helper functions.

## Capabilities

### Modified Capabilities

- `configuration-service`: Establish `BaseSettings.load_settings(...)` as the
  standard module settings activation path and ensure `ConfigField` transforms
  are consistently applied.
- `module-settings-access`: Modules with runtime settings expose a settings
  class that carries its `module_config` and can be loaded through
  `load_settings`.
- `site-startup-api`: Module setup should construct module settings through the
  settings class rather than ad hoc `ConfigService` parsing helpers.
- `environment-configuration`: Environment values and config-file values should
  pass through the same declared field transforms.

## Impact

- Reduces duplicated validation and normalisation code.
- Makes module setup easier to read and test.
- Prevents drift between runtime settings, tool settings, and validation paths.
- May require small public API cleanup where helper functions were previously
  exported for module settings.
- Should not introduce compatibility shims; this project is unreleased and the
  clean settings contract should replace older internal helper shapes.
