## ADDED Requirements

### Requirement: Application config boundary
The system SHALL require a resolved application config file for normal
environment/project configuration loading used by default app startup and
package-owned project commands.

#### Scenario: APP_CONFIG selects app configuration
- **WHEN** `APP_CONFIG` names an application config file
- **THEN** normal project command and default app startup configuration loading
  uses that file as the application config boundary

#### Scenario: Project app config is discovered
- **WHEN** no `APP_CONFIG` is set and a Wevra host project with `app.toml` can
  be resolved
- **THEN** normal project command and default app startup configuration loading
  uses that `app.toml` as the application config boundary

#### Scenario: Missing app config fails fast
- **WHEN** no `APP_CONFIG` or project `app.toml` can be resolved for normal
  project command or default app startup configuration loading
- **THEN** configuration loading fails with an actionable error instead of
  constructing application settings from built-in defaults

#### Scenario: Explicit settings construction remains available
- **WHEN** tests or specialised callers construct settings explicitly without
  using environment/project config loading
- **THEN** those explicit settings remain usable without requiring an
  application config file

### Requirement: Application database environment precedence
The system SHALL resolve application database URL values in a deterministic
order when loading settings from application config.

#### Scenario: Shared database override wins
- **WHEN** `DATABASE_URL` is set during application or auth settings loading
- **THEN** the application database URL comes from `DATABASE_URL`

#### Scenario: Auth-specific database override is not supported
- **WHEN** `AUTH_DATABASE_URL` is set and `DATABASE_URL` is not set during auth
  settings loading
- **THEN** the application database URL does not come from `AUTH_DATABASE_URL`

#### Scenario: Application database config is default
- **WHEN** `DATABASE_URL` is not set during application or auth settings
  loading
- **THEN** the application database URL comes from `database_url` in the
  resolved `[app]` config table

#### Scenario: Relative database paths are app-relative
- **WHEN** `[app].database_url` contains a relative SQLite file path
- **THEN** the path is resolved relative to the directory containing the loaded
  application config file
