## 1. Startup Environment Channel

- [x] 1.1 Define the effective startup environment mapping used between runserver and ASGI startup.
- [x] 1.2 Add startup environment parsing for `APP_ROOT`, `APP_CONFIG`, `DATABASE_URL`, and `APP_ENV` without host-app code involvement.
- [x] 1.3 Ensure direct `start()` and `start_site()` arguments take precedence over implicit process environment values unless an environment mapping is explicitly supplied.

## 2. Runserver CLI

- [x] 2.1 Add `--project`, `--config`, `--database-url`, and `--deploy` options to `wevra-runserver`.
- [x] 2.2 Resolve runserver startup overrides deterministically and write them into the server process environment before invoking Uvicorn.
- [x] 2.3 Preserve existing Uvicorn argument forwarding and app-target ownership checks.

## 3. Config And Path Resolution

- [x] 3.1 Update config-source normalisation so default `app.toml`, explicit config files, `APP_CONFIG`, and explicit project roots use `APP_ROOT` / `--project` as the only project-root override.
- [x] 3.2 Apply database URL and deployment environment overrides through central config precedence rather than direct database/auth mutation.
- [x] 3.3 Ensure runtime database setup, validation, and migration settings resolve relative SQLite paths from the same effective project root.

## 4. Tests And Documentation

- [x] 4.1 Add tests for default project-root discovery with `app.toml`.
- [x] 4.2 Add tests proving explicit config file selection does not change project root and explicit `--project` / `APP_ROOT` does.
- [x] 4.3 Add tests for `--database-url` overriding config and environment database values.
- [x] 4.4 Add tests for `--deploy` overriding config and environment deployment values.
- [x] 4.5 Update runserver/help documentation for startup override options and effective project-root rules.
- [x] 4.6 Refactor database capability tests and helper scaffolding to use public database capability APIs rather than private connection helpers.
- [x] 4.7 Add database URL resolver coverage for absolute SQLite URLs and non-SQLite URLs that must remain unchanged.
