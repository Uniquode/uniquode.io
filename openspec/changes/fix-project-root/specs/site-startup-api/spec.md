## ADDED Requirements

### Requirement: Runserver supplies startup overrides

Wevra runserver SHALL expose CLI options for startup-level configuration overrides and pass those overrides into Wevra startup without requiring host app boilerplate.

#### Scenario: Runserver accepts startup override options

- **WHEN** a developer starts `wevra-runserver` with `--project`, `--config`, `--database-url`, or `--deploy`
- **THEN** runserver records those values as Wevra startup overrides
- **AND** forwards them into the ASGI app startup path

#### Scenario: Runserver keeps Uvicorn ownership separate

- **WHEN** a developer passes Uvicorn-specific arguments after the runserver options
- **THEN** runserver continues to pass those arguments to Uvicorn
- **AND** it does not treat Uvicorn arguments as Wevra startup config overrides

### Requirement: Startup reads effective environment channel

Wevra startup SHALL read the effective startup environment selected by runserver or the invoking process when no explicit in-process startup arguments have been supplied.

#### Scenario: ASGI startup receives runserver overrides

- **WHEN** `wevra-runserver` starts an app through Uvicorn
- **AND** startup overrides were supplied to runserver
- **THEN** runserver exposes those overrides through `APP_ROOT`, `APP_CONFIG`, `DATABASE_URL`, and `APP_ENV` for the server process
- **AND** the imported ASGI app startup path uses those values to select the project root, config file, database URL, and deployment environment before module setup

#### Scenario: Explicit in-process startup inputs win

- **WHEN** a test or embedded caller passes explicit startup inputs directly to `start()` or `start_site()`
- **THEN** Wevra uses those direct inputs
- **AND** it does not override them with values from the process environment channel unless that environment was explicitly supplied by the caller
