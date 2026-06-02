## MODIFIED Requirements

### Requirement: User manager command
The system SHALL provide an `auth_ext`-owned CLI script named `identitymgr` for
administrative local identity management, including users, groups, scopes,
memberships, and effective-scope inspection.

#### Scenario: Project script exists
- **WHEN** a developer inspects project scripts
- **THEN** `identitymgr` is defined as a runnable project command
- **AND** `usermgr` is not defined as a project command

#### Scenario: Command uses identity foundation
- **WHEN** `identitymgr` performs user, group, scope, membership, or
  effective-scope operations
- **THEN** it uses the configured identity persistence and FastAPI
  Users/auth-extension identity services rather than duplicating password,
  user-lifecycle, or authorisation-scope logic

#### Scenario: Command loads generic auth configuration
- **WHEN** an operator supplies `--config path/to/auth.toml`
- **THEN** `identitymgr` reads identity configuration from the `[auth]` table in
  that file
- **AND** relative SQLite database paths are resolved relative to the config file
  directory

#### Scenario: Command supports database override
- **WHEN** `AUTH_DATABASE_URL` is set
- **THEN** `identitymgr` uses that database URL instead of the value from
  `[auth]`

#### Scenario: Scriptable output is available
- **WHEN** an operator requests JSON or CSV output
- **THEN** `identitymgr` emits the requested machine-readable format without
  password material
