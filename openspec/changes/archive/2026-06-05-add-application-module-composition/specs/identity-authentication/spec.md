## MODIFIED Requirements

### Requirement: FastAPI Users baseline integration
The system SHALL use FastAPI Users for the baseline local account lifecycle and
authentication primitives where they fit the project identity model, with
reusable identity routes, default identity templates, static assets, model
metadata, and identity migration revisions owned by `auth_ext` when that module
is installed.

#### Scenario: FastAPI Users dependency is present
- **WHEN** a developer inspects project runtime dependencies
- **THEN** FastAPI Users is included as a runtime dependency for identity
  foundation work

#### Scenario: Auth extension owns reusable identity presentation defaults
- **WHEN** local account lifecycle or authentication primitives need browser
  pages such as login, signup, verification, password reset, account, logout, or
  password change
- **THEN** `auth_ext` owns the reusable route surfaces and default
  `templates/identity` content for those pages

#### Scenario: Application includes identity surfaces intentionally
- **WHEN** the application wants to expose identity pages or APIs
- **THEN** it includes `auth_ext` in `modules` or enables an
  equivalent explicit integration rather than receiving routes through implicit
  package scanning

#### Scenario: Public-only application can omit identity surfaces
- **WHEN** the application omits `auth_ext` from `modules`
- **THEN** identity routes, identity templates, identity static assets,
  identity context providers, identity model metadata, and identity migration
  revisions are not loaded into that application instance

#### Scenario: Application keeps product ownership around identity flows
- **WHEN** FastAPI Users or `auth_ext` provides account lifecycle or
  authentication primitives
- **THEN** application code still owns account creation policy configuration,
  email delivery, redirects, product navigation, and application-specific error
  handling around those flows, while layout and theme defaults come from the
  composed web foundation or a host override

#### Scenario: Application can override identity templates
- **WHEN** the application supplies a template at the same logical path as an
  `auth_ext` default identity template
- **THEN** the application template is used without changing the `auth_ext`
  route or view implementation

#### Scenario: Application can override identity static assets
- **WHEN** the application supplies a static asset at the same logical path as
  an `auth_ext` default identity asset
- **THEN** the application asset is used without changing the `auth_ext` route
  or view implementation

### Requirement: Integration feature flag abstraction
The system SHALL gate optional identity integrations through an explicit
settings or feature-flag abstraction before exposing their routes or flows.

#### Scenario: Disabled integration routes are not exposed
- **WHEN** an optional identity integration such as OAuth account linking is
  disabled by the feature-flag abstraction
- **THEN** the application does not expose that integration's user-facing routes
  or flows

#### Scenario: Enabled integration routes are exposed intentionally
- **WHEN** an optional identity integration is enabled through the feature-flag
  abstraction and required provider configuration is present
- **THEN** the application exposes the corresponding integration routes or flows
  intentionally

#### Scenario: Feature flags do not replace policy checks
- **WHEN** an integration route is enabled through the feature-flag abstraction
- **THEN** account creation, account linking, and authorisation policy still
  apply through the identity and authorisation boundaries

#### Scenario: Reusable modules do not depend on application settings
- **WHEN** reusable identity modules need integration availability information
- **THEN** they depend on a protocol, callable, or module-local configuration
  object rather than importing the application's owned settings type

#### Scenario: Application settings adapt into integration options
- **WHEN** `uniquode` application settings contain identity integration flags
- **THEN** the application adapts those settings into a separate integration
  options object before passing them to reusable identity modules

#### Scenario: Route module inclusion does not bypass feature flags
- **WHEN** the application installs an identity route module
- **THEN** disabled optional identity integration routes remain unavailable
  unless their feature flag and required configuration are enabled
