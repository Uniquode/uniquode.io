## 1. Startup Override Channel

- [ ] 1.1 Define the Wevra-owned startup override payload and private channel used between runserver and ASGI startup.
- [ ] 1.2 Add startup override parsing that returns config source, project root, and database URL overrides without host-app code involvement.
- [ ] 1.3 Ensure direct `start()` and `start_site()` arguments take precedence over the startup channel.

## 2. Runserver CLI

- [ ] 2.1 Add `--project`, `--config`, and `--database-url` options to `wevra-runserver`.
- [ ] 2.2 Resolve runserver startup overrides deterministically and write them into the Wevra startup channel before invoking Uvicorn.
- [ ] 2.3 Preserve existing Uvicorn argument forwarding and app-target ownership checks.

## 3. Config And Path Resolution

- [ ] 3.1 Update config-source normalisation so default `app.toml`, explicit config files, `APP_CONFIG`, and explicit project roots produce one effective project root.
- [ ] 3.2 Apply database URL overrides through central config precedence rather than direct database/auth mutation.
- [ ] 3.3 Ensure runtime database setup, validation, and migration settings resolve relative SQLite paths from the same effective project root.

## 4. Tests And Documentation

- [ ] 4.1 Add tests for default project-root discovery with `app.toml`.
- [ ] 4.2 Add tests for explicit config file root behaviour and explicit `--project` override behaviour.
- [ ] 4.3 Add tests for `--database-url` overriding config and environment database values.
- [ ] 4.4 Update runserver/help documentation for startup override options and effective project-root rules.
- [ ] 4.5 Refactor database capability tests and helper scaffolding to use public database capability APIs rather than private connection helpers.
- [ ] 4.6 Add database URL resolver coverage for absolute SQLite URLs and non-SQLite URLs that must remain unchanged.
