## Why

Runtime testing exposed that Wevra startup does not have a clear enough contract for project-root, config-file, and runtime override resolution. Relative paths such as SQLite database URLs can therefore point at a different file between migration tooling and the running ASGI app, producing confusing runtime failures.

## What Changes

- Define an explicit effective project-root rule for Wevra startup and project tools.
- Keep `app.toml` as the default application config filename.
- Treat the current/runtime project directory as the default root when using default `app.toml` discovery.
- Add `wevra-runserver` options for startup overrides, including `--project`, `--config`, `--database-url`, and `--deploy`.
- Use the existing startup environment channel so runserver CLI values override environment values, and environment values override defaults.
- `--project` maps to `APP_ROOT`, `--config` maps to `APP_CONFIG`, `--database-url` maps to `DATABASE_URL`, and `--deploy` maps to `APP_ENV`.
- Ensure `APP_CONFIG` selects the config file only and does not override project root.
- Ensure runtime database URL resolution, validation, and migration tooling use the same effective project root.
- Keep static and template root override flags out of scope; static collection is handled by the separate collect work, and template roots are not a current runtime override requirement.
- Note that a Wevra factory may replace the environment bridge later, but this change keeps the implementation small and compatible with Uvicorn import/reload semantics.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `site-startup-api`: define startup override handling and the Wevra-owned startup config channel used by runserver and ASGI startup.
- `environment-configuration`: update relative database path resolution to use the effective project root rather than the application config file directory unconditionally.

## Impact

- Affected code: Wevra startup, runserver tooling, config source normalisation, database URL resolution, validation/migration settings loading, and related tests.
- Affected APIs: `wevra-runserver` gains explicit startup override options.
- No new runtime dependency is required.
- Tracking: [UT-241](https://linear.app/uniquode/issue/UT-241/fix-project-root-and-startup-override-handling)
