## ADDED Requirements

### Requirement: Application-scoped auth configuration
The system SHALL configure reusable `wevra.auth` runtime and password policy
settings through the host application configuration file for normal
Wevra-hosted operation, while auth persistence uses the host application's
configured database URL.

#### Scenario: Auth configuration lives in app config
- **WHEN** a host application configures reusable auth behaviour
- **THEN** the configuration is expressed in `[auth]` and
  `[auth.password.policy]` tables in the application config file
- **AND** standalone auth-only config files are not required for normal
  operation

#### Scenario: Password policy uses application auth config
- **WHEN** `[auth.password.policy]` is present in the resolved application
  config file
- **THEN** reusable auth password writes use those configured thresholds for the
  default password policy

#### Scenario: Auth persistence uses application database config
- **WHEN** `[app].database_url` is present in the resolved application config
  file and no database environment override applies
- **THEN** reusable auth services use that database URL for identity persistence

#### Scenario: Reusable auth remains app-contextual
- **WHEN** reusable auth services are used by a Wevra-hosted application
- **THEN** they are configured through the host application's resolved app
  configuration boundary rather than through a package-global standalone auth
  configuration boundary
