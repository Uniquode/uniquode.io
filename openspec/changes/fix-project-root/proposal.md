## Why

Runtime testing exposed that Wevra startup does not have a clear enough contract for project-root, config-file, and runtime override resolution. Relative paths such as SQLite database URLs can therefore point at a different file between migration tooling and the running ASGI app, producing confusing runtime failures.

## What Changes

- Define an explicit effective project-root rule for Wevra startup and project tools.
- Keep `app.toml` as the default application config filename.
- Treat the current/runtime project directory as the default root when using default `app.toml` discovery.
- Treat an explicit config file supplied by CLI or `APP_CONFIG` as a startup boundary that can establish the project root from the config file location unless `--project` overrides it.
- Add `wevra-runserver` options for startup overrides, including `--project`, `--config`, and `--database-url`.
- Add a Wevra-owned startup config channel that lets `wevra-runserver` pass those overrides into the ASGI app startup path without app-owned boilerplate.
- Ensure runtime database URL resolution, validation, and migration tooling use the same effective project root.

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
