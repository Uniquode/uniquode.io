## MODIFIED Requirements

### Requirement: Global web resource roots
The system SHALL provide application-owned default template and static resource
override roots while supporting installed module package template and static
asset sources in the same logical namespaces.

#### Scenario: Application template root has a settings-backed default
- **WHEN** a developer inspects the project settings or rendering configuration
- **THEN** the application defines a configurable application Jinja2 template
  root with a default value of `src/templates/`

#### Scenario: Installed modules can add package template sources
- **WHEN** the application installs modules that declare package templates
- **THEN** the renderer includes those package template sources after the
  application template root

#### Scenario: Global static root has a settings-backed default
- **WHEN** a developer inspects the project settings or static asset
  configuration
- **THEN** the application defines a configurable application static asset root
  with a default value of `src/static/`

#### Scenario: Installed modules can add package static sources
- **WHEN** the application installs modules that declare package static assets
- **THEN** the static asset resolver includes those package static sources after
  the application static root

#### Scenario: Static route prefix has a settings-backed default
- **WHEN** a developer inspects the project settings or static asset
  configuration
- **THEN** the application defines a configurable static route prefix with a
  default value of `/static/`

### Requirement: Template hierarchy and reusable components
The system SHALL provide a baseline logical template hierarchy and reusable
server-rendered component structure for HTML pages, allowing application
templates to override installed module package templates by logical path.

#### Scenario: Base template hierarchy exists
- **WHEN** a developer inspects the initial template set
- **THEN** it includes a ubiquitous base page template and a base HTML error
  template in the application template root

#### Scenario: Shared components have a conventional location
- **WHEN** a developer inspects the template tree
- **THEN** shared application-owned reusable components live under the logical
  path `components/`

#### Scenario: Module-local components are supported
- **WHEN** an installed module introduces reusable templates that are primarily
  local to that module
- **THEN** the module can publish those templates from its package template
  source under logical paths such as `<module-base>/components/`

#### Scenario: Application override keeps logical path stable
- **WHEN** the application overrides a module-provided template
- **THEN** it supplies the replacement at the same logical template path in the
  application template root

### Requirement: Static assets and style resources
The system SHALL support application-owned static overrides and installed module
package static defaults in a single logical static namespace that can be served
at runtime or exported by tooling.

#### Scenario: Application-owned style assets remain available
- **WHEN** a browser requests an application-owned static asset such as
  `styles/app.css`
- **THEN** the static route serves the asset from the application static root

#### Scenario: Module-owned static assets are available
- **WHEN** an installed module publishes package static assets
- **THEN** the static route can serve those assets by logical path

#### Scenario: Application static override keeps logical path stable
- **WHEN** the application overrides a module-provided static asset
- **THEN** it supplies the replacement at the same logical static path in the
  application static root

#### Scenario: Static namespace can be exported
- **WHEN** a collectstatic-style tool exports the logical static namespace
- **THEN** it uses the same application-first and module precedence rules as
  runtime static serving

### Requirement: HTML requests use a dispatcher protocol
The system SHALL provide an internal HTML request-dispatch layer under FastAPI
for page-oriented handlers, with route definitions composed from explicitly
installed application modules.

#### Scenario: HTML views register declaratively
- **WHEN** a developer adds a page-oriented HTML view
- **THEN** the view registers through the HTML dispatcher mechanism rather than
  requiring a one-route-per-page decorator pattern

#### Scenario: Route definitions are declared in feature modules
- **WHEN** a feature module declares page or partial routes
- **THEN** the module exposes declarative route definitions through its route
  module rather than requiring the application to duplicate each route

#### Scenario: Application installs feature module routes explicitly
- **WHEN** the application includes a module in `installed_modules`
- **THEN** the dispatcher registers that module's page and partial routes in
  configured order

#### Scenario: Dispatcher selects a matching view
- **WHEN** an HTML request reaches the dispatcher entry point
- **THEN** the dispatcher evaluates the registered HTML views against the
  request and selects the final view deterministically

#### Scenario: Selected view serves the response
- **WHEN** the dispatcher has selected an HTML view
- **THEN** it passes the full request to that view's serving operation and
  returns the resulting response

### Requirement: Web-structure validation is available
The system SHALL provide an initial validation surface for the web foundation
that can detect structural errors across application and installed module web
resources before runtime.

#### Scenario: Validation command checks implemented web structure
- **WHEN** a developer runs the documented web-structure validation command
- **THEN** the command inspects implemented route, template, static asset,
  installed module, package template, package static, and
  template-context-provider structures and reports detected errors

#### Scenario: Broken references fail validation
- **WHEN** an implemented route, template reference, package template
  reference, static asset reference, context provider reference, or module
  surface reference cannot be resolved by the validation surface
- **THEN** the validation command reports the failure instead of silently
  succeeding
