## Why

The host app `Settings` object has become an aggregate container for dependency-owned configuration, such as Wevra auth `IdentityOptions`. Now that configuration is centralised behind `wevra.config`, modules should own their typed settings and expose access through a small protocol rather than bloating the host app settings object.

## What Changes

- Refactor host app settings so `app.settings.Settings` contains only host-owned runtime policy and values.
- Introduce a module-owned settings access pattern where each module defines and loads its own typed settings from the central configuration service.
- Define how modules that need another module's settings request them from the owning module rather than reaching into the host app aggregate.
- Preserve central raw configuration loading through `wevra.config`; module settings loaders perform module-specific coercion, validation, defaults, and policy checks close to use.
- Preserve explicit host app settings construction for tests and specialised callers.
- Avoid moving dependency settings into the host app unless the value is genuinely host-owned policy.

## Capabilities

### New Capabilities

- `module-settings-access`: Defines module-owned typed settings access over central configuration, including ownership boundaries, cross-module access, and host app settings scope.

### Modified Capabilities

- `environment-configuration`: Refines configuration consumption so central raw config is the shared substrate while typed settings belong to their owning module, not to an app-wide aggregate object.

## Impact

- Linear: [UT-237](https://linear.app/uniquode/issue/UT-237/refactor-app-settings)
- Affected code: `app/src/app/settings.py`, app startup/composition, `wevra.auth` settings access, and any module initialisation code that currently reads dependency settings through the app settings object.
- Affected architecture: configuration ownership boundaries between the host app and reusable Wevra modules.
- Tests should move dependency settings assertions into the owning module where practical, keeping app tests focused on host-owned wiring and integration boundaries.
- No new runtime dependency is expected.
