## MODIFIED Requirements

### Requirement: Standalone addon package
The system SHALL introduce `fastapi-users-auth-ext` as a standalone FastAPI
Users addon that is independent of the `uniquode` application while allowing the
addon to publish reusable identity routes and default package templates.

#### Scenario: Addon does not import application code
- **WHEN** a developer inspects the addon package
- **THEN** it does not import from `uniquode` or depend on application settings,
  models, route modules, or application-owned templates

#### Scenario: Addon can publish package templates
- **WHEN** the addon owns reusable identity page or partial defaults
- **THEN** those templates are packaged under the addon and exposed through the
  host application's template-source composition mechanism

#### Scenario: Python package name is importable
- **WHEN** addon code is imported from Python
- **THEN** the import package uses the valid Python package name `auth_ext`

### Requirement: FastAPI Users extension boundary
The addon SHALL extend FastAPI Users through public route, dependency,
user-manager, authentication-backend, and module web-composition integration
points.

#### Scenario: Addon supplements selected flows
- **WHEN** the addon implements an advanced authentication flow
- **THEN** it uses FastAPI Users user and authentication abstractions where they
  fit rather than reimplementing the baseline user lifecycle

#### Scenario: Route replacement is explicit
- **WHEN** an addon flow must replace a FastAPI Users route such as login
- **THEN** the application includes the addon route module or router
  intentionally instead of registering duplicate method/path combinations that
  depend on route-order behaviour

#### Scenario: Addon publishes identity route module
- **WHEN** the addon provides reusable identity pages, partials, or APIs
- **THEN** it exposes them through a host-enabled route module rather than by
  mutating the host application automatically

### Requirement: UI-independent flows
The addon SHALL avoid imposing product UI assumptions while allowing reusable
default identity templates to be overridden by the host application.

#### Scenario: Addon routes are host-enabled
- **WHEN** the addon exposes routes or flow helpers
- **THEN** the host application includes those routes intentionally and remains
  in control of where they are mounted

#### Scenario: Addon templates do not own product shell
- **WHEN** the addon ships default identity templates
- **THEN** those templates render identity content and forms without owning
  application theme, branding, product navigation, or layout chrome

#### Scenario: Application can override addon templates
- **WHEN** the application supplies a template at the same logical path as an
  addon default
- **THEN** the application template is used instead of the addon template

#### Scenario: Application controls user-facing product policy
- **WHEN** a flow needs deployment-specific page copy, email content, redirects,
  delivery integration, throttling, or product policy
- **THEN** the application supplies that policy or override through the addon
  configuration and web-composition boundaries
