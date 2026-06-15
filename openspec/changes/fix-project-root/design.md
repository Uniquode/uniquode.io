## Context

The root workspace project is `/Users/davidn/Code/uniquode`; the app package lives below `app/`, and Wevra is a workspace member below `wevra/`. Runtime paths must not accidentally resolve relative to the Wevra package checkout, and working files such as SQLite databases must not be assumed to live inside the app module package.

Current startup behaviour is split across `wevra-runserver`, ASGI app loading, `start_site()`, file config loading, environment loading, database setup, migration tooling, and validation tooling. The absence of one explicit startup channel makes CLI overrides difficult to pass into the imported ASGI app without leaking Wevra concerns into host app code.

## Goals / Non-Goals

**Goals:**

- Make effective project-root resolution deterministic.
- Keep cwd/runtime project root as the normal default when default `app.toml` discovery is used.
- Allow explicit config-file selection to establish the app boundary when supplied through CLI or `APP_CONFIG`.
- Allow `--project` to override the effective project root explicitly.
- Allow `--database-url` to override configured database URLs for local runtime testing.
- Pass runserver startup overrides through a Wevra-owned channel read by ASGI startup.
- Keep host app code free of Wevra startup/config plumbing.

**Non-Goals:**

- Do not introduce generic dynamic configuration watching.
- Do not make host apps manipulate Wevra database/auth settings directly.
- Do not add compatibility shims for old startup behaviour.
- Do not introduce a generic `--set section.key=value` override surface in this change.

## Decisions

### Decision: Effective project root is explicit startup state

The effective project root is a startup-level value. It defaults from the runtime project root when default config discovery is used. If an explicit config path is supplied and no project root override is supplied, the config file location can establish the project root. If `--project` is supplied, it wins.

Alternative considered: always resolve relative paths from the config file directory. This was rejected because app packages can be configured from workspace metadata or module composition, and working files do not belong inside Python module package directories by default.

### Decision: Runserver writes a Wevra-owned startup channel

`wevra-runserver` will serialise startup override values into a private Wevra-owned channel that the imported ASGI app startup code reads before calling `start_site()`. This avoids app-owned boilerplate and avoids trying to pass Python objects through Uvicorn's import boundary.

Alternative considered: mutate generic process environment variables such as `APP_CONFIG` and `DATABASE_URL` only. This is too imprecise because those variables have broader semantics and do not carry the effective project root as one coherent startup decision.

### Decision: Database URL overrides remain config inputs

`--database-url` is treated as a startup config override for `[app].database_url`, not as a direct auth or database runtime mutation. Database, auth, validation, and migration consumers must all see the same effective value through central config resolution.

Alternative considered: make runserver patch database setup directly. This was rejected because runserver should not know database/auth internals.

## Risks / Trade-offs

- [Risk] Existing local databases may appear to move when the corrected root rule is applied. -> Mitigation: document the effective root rule and require explicit `--project` or database URL when the location matters.
- [Risk] CLI and ASGI startup can diverge if only one path reads the startup channel. -> Mitigation: centralise startup override parsing in Wevra and cover runserver/startup with tests.
- [Risk] `APP_CONFIG` semantics can be confused with project-root semantics. -> Mitigation: treat `APP_CONFIG` as config file selection only; project root is a separate effective startup value.
