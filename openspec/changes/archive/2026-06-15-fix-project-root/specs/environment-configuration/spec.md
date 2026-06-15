## MODIFIED Requirements

### Requirement: Application config boundary

The system SHALL require a resolved application config file for normal environment/project configuration loading used by default app startup and package-owned project commands.

#### Scenario: APP_CONFIG selects app configuration

- **WHEN** `APP_CONFIG` names an application config file
- **THEN** normal project command and default app startup configuration loading uses that file as the application config boundary
- **AND** relative `APP_CONFIG` values are resolved from the effective project root
- **AND** `APP_CONFIG` does not change the effective project root

#### Scenario: Project app config is discovered

- **WHEN** no `APP_CONFIG` is set and a Wevra host project with `app.toml` can be resolved
- **THEN** normal project command and default app startup configuration loading uses that `app.toml` as the application config boundary
- **AND** the effective project root is the runtime project root used to locate that default config file

#### Scenario: Explicit project root wins

- **WHEN** startup supplies an explicit project root through `--project` or `APP_ROOT`
- **THEN** normal project command and default app startup configuration loading uses that project root for relative path resolution
- **AND** the config file path does not replace the explicit project root

#### Scenario: Missing app config fails fast

- **WHEN** no `APP_CONFIG` or project `app.toml` can be resolved for normal project command or default app startup configuration loading
- **THEN** configuration loading fails with an actionable error instead of constructing application settings from built-in defaults

#### Scenario: Explicit settings construction remains available

- **WHEN** tests or specialised callers construct settings explicitly without using environment/project config loading
- **THEN** those explicit settings remain usable without requiring an application config file

### Requirement: Application database environment precedence

The system SHALL resolve application database URL values in a deterministic order when loading settings from application config.

#### Scenario: CLI database override wins

- **WHEN** startup supplies an explicit database URL override
- **THEN** the application database URL comes from that startup override
- **AND** database, auth, validation, and migration consumers observe the same effective value

#### Scenario: Shared database override wins

- **WHEN** `DATABASE_URL` is set during application or auth settings loading
- **AND** no startup database URL override was supplied
- **THEN** the application database URL comes from `DATABASE_URL`

#### Scenario: Auth-specific database override is not supported

- **WHEN** `AUTH_DATABASE_URL` is set and `DATABASE_URL` is not set during auth settings loading
- **THEN** the application database URL does not come from `AUTH_DATABASE_URL`

#### Scenario: Application database config is default

- **WHEN** no startup database override or `DATABASE_URL` is set during application or auth settings loading
- **THEN** the application database URL comes from `database_url` in the resolved `[app]` config table

#### Scenario: Relative database paths use effective project root

- **WHEN** the effective application database URL contains a relative SQLite file path
- **THEN** the path is resolved relative to the effective project root
- **AND** it is not resolved relative to the Wevra package root or an accidental process current directory

## ADDED Requirements

### Requirement: Deployment environment startup override

The system SHALL allow runserver startup to override the effective application deployment environment through the `--deploy` option.

#### Scenario: CLI deployment override wins

- **WHEN** startup supplies a deployment environment through `--deploy`
- **THEN** the effective application deployment environment comes from that startup override
- **AND** auth, CSRF, validation, and other deployment-policy consumers observe the same effective value

#### Scenario: Config deployment value is default

- **WHEN** no startup deployment override is supplied
- **THEN** the effective application deployment environment comes from configured application/environment sources
