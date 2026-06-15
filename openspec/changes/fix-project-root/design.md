## Context

The root workspace project is `/Users/davidn/Code/uniquode`; the app package lives below `app/`, and Wevra is a workspace member below `wevra/`. Runtime paths must not accidentally resolve relative to the Wevra package checkout, and working files such as SQLite databases must not be assumed to live inside the app module package.

Current startup behaviour is split across `wevra-runserver`, ASGI app loading, `start_site()`, file config loading, environment loading, database setup, migration tooling, and validation tooling. The absence of one explicit startup channel makes CLI overrides difficult to pass into the imported ASGI app without leaking Wevra concerns into host app code.

## Goals / Non-Goals

**Goals:**

- Make effective project-root resolution deterministic.
- Keep cwd/runtime project root as the normal default when default `app.toml` discovery is used.
- Allow explicit config-file selection through CLI or `APP_CONFIG` without changing the effective project root.
- Allow `--project` / `APP_ROOT` to override the effective project root explicitly.
- Allow `--database-url` to override configured database URLs for local runtime testing.
- Allow `--deploy` to override the effective deployment environment without using the longer `--deployment-environment` flag or ambiguous `--environment` wording.
- Pass runserver startup overrides through the existing startup environment channel read by ASGI startup.
- Keep host app code free of Wevra startup/config plumbing.

**Non-Goals:**

- Do not introduce generic dynamic configuration watching.
- Do not make host apps manipulate Wevra database/auth settings directly.
- Do not add compatibility shims for old startup behaviour.
- Do not introduce a generic `--set section.key=value` override surface in this change.
- Do not add static-root or template-root runserver flags in this change.

## Decisions

### Decision: Effective project root is explicit startup state

The effective project root is a startup-level value. It defaults from the runtime project root when default config discovery is used. `--project` / `APP_ROOT` is the only mechanism that changes the effective project root. `--config` / `APP_CONFIG` selects the config file and does not change root.

Alternative considered: resolving relative paths from the config file directory. This was rejected because app packages can be configured from workspace metadata or module composition, and working files do not belong inside Python module package directories by default.

### Decision: Runserver uses the existing startup environment channel

`wevra-runserver` will set normal startup environment values before invoking Uvicorn: `APP_ROOT`, `APP_CONFIG`, `DATABASE_URL`, and `APP_ENV`. This gives the desired precedence of CLI flags over environment variables over defaults, and it works with Uvicorn import/reload semantics without host-app boilerplate.

Alternative considered: a private serialised startup payload. This was rejected because the existing environment channel is simpler, visible, and already maps to the required values. A Wevra factory remains the likely future direction, but it is not required for this change.

### Decision: Database URL overrides remain config inputs

`--database-url` is treated as a startup config override for `[app].database_url`, not as a direct auth or database runtime mutation. Database, auth, validation, and migration consumers must all see the same effective value through central config resolution.

Alternative considered: make runserver patch database setup directly. This was rejected because runserver should not know database/auth internals.

### Decision: Deployment environment override uses `--deploy`

`--deploy` will set the effective `[app].deployment_environment` value for startup. The longer `--deployment-environment` spelling is unnecessarily verbose for a common command-line option, and `--environment` is ambiguous because it could mean dotenv loading, process environment, deployment stage, or app mode.

Static-root and template-root flags are intentionally deferred. Static handling belongs with the planned collect command, and template root override does not currently solve a concrete runtime testing problem.

## Risks / Trade-offs

- [Risk] Existing local databases may appear to move when the corrected root rule is applied. -> Mitigation: document the effective root rule and require explicit `--project` or database URL when the location matters.
- [Risk] CLI and ASGI startup can diverge if only one path reads the startup channel. -> Mitigation: centralise startup override parsing in Wevra and cover runserver/startup with tests.
- [Risk] `APP_CONFIG` semantics can be confused with project-root semantics. -> Mitigation: treat `APP_CONFIG` as config file selection only; `APP_ROOT` / `--project` is the separate effective startup root value.
