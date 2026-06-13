## Why

The host app still contains leftover framework/configuration/environment scaffolding from before Wevra owned site startup and module composition. This makes the app look more complex than a Wevra app should be, keeps reusable concerns in the wrong package, and obscures whether modules are using the configuration protocol correctly.

This change makes the app pristine: anything not genuinely app-specific is either moved into the owning Wevra module/platform API or removed completely.

## What Changes

- Audit current app files and remove or relocate leftover Wevra scaffolding, with immediate focus on:
  - `app/src/app/config_definitions.py`
  - `app/src/app/environment.py`
  - app-level validation that duplicates Wevra/module validation
  - app `Settings` fields that exist only to bridge Wevra-owned concerns
- Move reusable configuration definition helpers, environment loading, environment parsing/validation, and config-to-settings bridge logic into Wevra where they are still needed.
- Remove app-owned environment loading as a normal requirement for a Wevra site. A generated/basic app should not need an `environment.py` file.
- Keep only product-specific app code in the app package: app-owned route surfaces, views, context, and genuinely product-specific settings.
- Ensure configured modules own their own configuration definitions and read config through Wevra config services instead of relying on app-aggregated settings.
- Challenge and simplify current `envex.Env` usage. If Wevra only needs environment lookup plus bool/int/path parsing and dotenv loading, expose that directly through a simpler Wevra-owned abstraction instead of requiring each app to wrap `envex`.
- Preserve the ability for a Wevra application to run without `wevra.db`, auth, or any specific Wevra feature module. Absence of module/configuration must mean absence, not fallback behaviour.
- **BREAKING**: App-owned configuration/environment adapter files and settings fields that exist only for Wevra-owned concerns will be removed or replaced by Wevra-owned APIs.

## Capabilities

### New Capabilities

### Modified Capabilities

- `application-infrastructure`: Tightens the app boundary so the host app contains only app-specific startup, route, view, context, and product settings code.
- `configuration-service`: Moves reusable configuration definition, environment source, and environment parsing support into Wevra and requires modules to use the config service boundary for their own settings.
- `environment-configuration`: Removes the requirement for host apps to own environment loading and clarifies what Wevra environment support actually provides.
- `module-settings-access`: Prevents the app from aggregating Wevra-owned module settings and requires public capability/config access at module boundaries.

## Impact

- Removes or rewrites app files that are currently architectural leftovers, especially `config_definitions.py` and `environment.py`.
- May move shared helpers into Wevra configuration/environment modules.
- Simplifies app `Settings` to app-owned values only.
- Requires tests proving the app still starts through Wevra startup, configured modules still receive their config, and a site can run without database/auth modules unless explicitly configured.
- May remove `envex` from app-facing code paths or encapsulate it fully inside Wevra if it remains useful internally.
