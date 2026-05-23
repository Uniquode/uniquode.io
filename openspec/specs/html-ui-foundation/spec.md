# html-ui-foundation Specification

## Purpose
Define the baseline HTML-first UI foundation for server-rendered pages, shared templates, semantic theming, and progressive enhancement in the `uniquode` application.

## Requirements

### Requirement: Global web resource roots
The system SHALL provide one global template root, one global static asset root, and one static route prefix for the HTML-first UI foundation, with all three values configurable through project settings.

#### Scenario: Global template root has a settings-backed default
- **WHEN** a developer inspects the project settings or rendering configuration
- **THEN** the application defines a configurable global Jinja2 template root with a default value of `src/templates/`

#### Scenario: Global static root has a settings-backed default
- **WHEN** a developer inspects the project settings or static asset configuration
- **THEN** the application defines a configurable global static asset root with a default value of `src/static/`

#### Scenario: Static route prefix has a settings-backed default
- **WHEN** a developer inspects the project settings or static asset configuration
- **THEN** the application defines a configurable static route prefix with a default value of `/static/`

### Requirement: Template hierarchy and reusable components
The system SHALL provide a baseline template hierarchy and reusable server-rendered component structure for HTML pages.

#### Scenario: Base template hierarchy exists
- **WHEN** a developer inspects the initial template set
- **THEN** it includes a ubiquitous base page template and a base HTML error template

#### Scenario: Shared components have a conventional location
- **WHEN** a developer inspects the template tree
- **THEN** shared reusable components live under `src/templates/components/`

#### Scenario: Module-local components are supported
- **WHEN** a feature module introduces reusable templates that are primarily local to that module
- **THEN** the templates may live under a conventional path such as `src/templates/<module-base>/components/`

### Requirement: HTML route surfaces are explicit
The system SHALL keep page routes, partial routes, and API routes as distinct route surfaces.

#### Scenario: Page route renders a full template
- **WHEN** a browser requests a page route
- **THEN** the handler returns a full HTML page response rendered from the template system

#### Scenario: Partial route renders a fragment
- **WHEN** a browser requests a partial route intended for `htmx`
- **THEN** the handler returns an HTML fragment response rather than a full page shell

#### Scenario: API route stays machine-oriented
- **WHEN** a client requests a route under `/api/`
- **THEN** the handler returns a machine-oriented response rather than a template-rendered HTML page

### Requirement: HTML requests use a dispatcher protocol
The system SHALL provide an internal HTML request-dispatch layer under FastAPI for page-oriented handlers.

#### Scenario: HTML views register declaratively
- **WHEN** a developer adds a page-oriented HTML view
- **THEN** the view registers through the HTML dispatcher mechanism rather than requiring a one-route-per-page decorator pattern

#### Scenario: Route definitions are declared in feature modules
- **WHEN** a feature module such as `site` declares its page routes
- **THEN** the module exposes declarative route definitions that bind route metadata to registered views in the dispatcher

#### Scenario: Dispatcher selects a matching view
- **WHEN** an HTML request reaches the dispatcher entry point
- **THEN** the dispatcher evaluates the registered HTML views against the request and selects the final view deterministically

#### Scenario: Selected view serves the response
- **WHEN** the dispatcher has selected an HTML view
- **THEN** it passes the full request to that view's serving operation and returns the resulting response

### Requirement: Static asset serving is separate from HTML dispatch
The system SHALL keep static asset serving separate from the HTML dispatcher.

#### Scenario: Static request uses static-serving path
- **WHEN** a client requests a path under the configured static URL prefix
- **THEN** the request is handled by the configured static-serving mechanism rather than by the HTML dispatcher

#### Scenario: Static URL contract supports production offload
- **WHEN** production infrastructure serves static assets directly
- **THEN** the configured static URL prefix remains valid without requiring the HTML dispatcher to serve those asset bytes

### Requirement: Baseline UI assets are delivered without a front-end build pipeline
The system SHALL provide the initial CSS and dynamic-enhancement baseline without requiring npm or another front-end build step.

#### Scenario: Pico CSS is available for MVP
- **WHEN** a rendered page loads the baseline stylesheet
- **THEN** Pico CSS is provided through the configured lightweight delivery approach for MVP

#### Scenario: htmx is available for progressive enhancement
- **WHEN** a rendered page uses `htmx` behaviour
- **THEN** the client receives `htmx` without requiring a front-end build pipeline

#### Scenario: Project CSS remains separate
- **WHEN** the application adds project-specific styles
- **THEN** those styles are layered separately from the baseline Pico CSS resource

### Requirement: Theme-aware styling is semantic across templates
The system SHALL apply theme-aware styling through semantic design roles and tokens across the HTML foundation rather than through template-local light or dark colour assumptions.

#### Scenario: Base templates consume semantic styling roles
- **WHEN** a developer inspects the base page templates and shared components
- **THEN** they rely on semantic styling roles such as background, surface, text, muted text, border, and accent rather than hard-coded mode-specific colour choices in template markup

#### Scenario: Theme mode changes token values rather than template structure
- **WHEN** the active theme mode changes between `auto`, `light`, and `dark`
- **THEN** the visual change is achieved by changing semantic token values and inherited styling rather than by branching the template structure per mode

#### Scenario: Project CSS defines mode-aware semantic tokens
- **WHEN** a developer inspects the project-specific stylesheet layer
- **THEN** the stylesheet defines semantic theme tokens or equivalent variables that support `auto`, `light`, and `dark` behaviour for the shared HTML foundation

### Requirement: Web-structure validation is available
The system SHALL provide an initial validation surface for the web foundation that can detect structural errors before runtime.

#### Scenario: Validation command checks implemented web structure
- **WHEN** a developer runs the documented web-structure validation command
- **THEN** the command inspects the implemented route, template, and static asset structures and reports detected errors

#### Scenario: Broken references fail validation
- **WHEN** an implemented route, template reference, or static asset reference cannot be resolved by the validation surface
- **THEN** the validation command reports the failure instead of silently succeeding
