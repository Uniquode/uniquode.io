## ADDED Requirements

### Requirement: Host app contains only app-owned site code
The host app SHALL contain only app-specific startup, route surfaces, views, context, and product settings. Generic Wevra configuration, environment loading, validation, module setup, database/auth/web setup, route discovery, route registration, static composition, and template composition SHALL be owned by Wevra or by the configured module that owns the concern.

#### Scenario: Basic app has no Wevra environment adapter
- **WHEN** a basic Wevra host app is inspected
- **THEN** it does not require an app-owned `environment.py` or equivalent wrapper to load Wevra configuration
- **AND** Wevra-owned tools load environment/configuration through Wevra-owned sources or explicit configured module definitions

#### Scenario: Basic app has no Wevra config aggregation file
- **WHEN** a basic Wevra host app is inspected
- **THEN** it does not require an app-owned `config_definitions.py` file for Wevra-owned settings
- **AND** reusable configuration definitions are declared by Wevra or the owning module

#### Scenario: App can omit database and auth modules
- **WHEN** app configuration omits `wevra.db` or `wevra.auth`
- **THEN** startup does not register database or auth capabilities for the omitted modules
- **AND** startup does not synthesise fallback database or auth configuration

#### Scenario: App tests cover app ownership only
- **WHEN** app tests inspect startup and settings behaviour
- **THEN** they assert app-owned route, view, context, and product settings outcomes
- **AND** they do not duplicate Wevra-owned config, environment, auth, database, static, or template internals


### Requirement: Basic app exposes app-owned route, view, context, and validation examples
A cleaned basic app SHALL keep app-owned route assembly, view handlers, request context helpers, and product validation in small explicit modules without framework boilerplate packages.

#### Scenario: Home page view is app-owned
- **WHEN** the app route surface is inspected
- **THEN** the home page handler lives in the app view module
- **AND** route assembly registers that handler through the app route module

#### Scenario: Home context is app-owned
- **WHEN** the home page view needs product context
- **THEN** the context helper lives in the app context module

#### Scenario: App validation is product-specific
- **WHEN** the app exposes validation targets
- **THEN** they validate app-owned product concerns such as the home route, health route, home page template, and static assets
- **AND** they do not validate Wevra-owned environment, database, auth, static, template, or route composition internals

#### Scenario: Health endpoint is included in the basic app
- **WHEN** a basic app route surface is generated or inspected
- **THEN** it includes a simple app-owned health endpoint

#### Scenario: Optional app setup hook is visible
- **WHEN** a basic app module is generated or inspected
- **THEN** it exposes a documented no-op `setup_site` hook from the app startup module
- **AND** the documentation explains that the stub is optional and may be removed when the app has no app-specific startup work

#### Scenario: App context provider composes request template context
- **WHEN** the basic app contributes template context
- **THEN** it exposes a context provider that accepts the request and existing template context
- **AND** it returns a new template context containing app-owned additions
- **AND** it does not mutate a raw context dictionary in place


### Requirement: Wevra owns reusable web request and static setup
Wevra SHALL own reusable template request context setup and runtime static file serving for composed sites.

#### Scenario: Request context is provided by default
- **WHEN** Wevra web setup handles a template-rendering request
- **THEN** the immutable per-request template context includes the current request by default
- **AND** templates can inspect request URL, path, and connection attributes

#### Scenario: Template context providers accumulate immutably
- **WHEN** Wevra assembles template context providers for a request
- **THEN** it initialises an empty `TemplateContext`
- **AND** each provider receives the request and current `TemplateContext`
- **AND** each provider returns a new `TemplateContext`
- **AND** the final render boundary converts the accumulated context to a plain mapping for templates

#### Scenario: Request context can be disabled
- **WHEN** the Wevra web request-context setting is explicitly disabled
- **THEN** Wevra does not inject the current request into template context

#### Scenario: Filesystem static handling is Wevra-owned
- **WHEN** a static root is configured
- **THEN** Wevra constructs the runtime static file ASGI app
- **AND** the host app does not construct or inject `StaticFiles`

#### Scenario: No static root means no filesystem static serving
- **WHEN** no static root is configured
- **THEN** Wevra does not enable filesystem static serving for the host app

#### Scenario: ASGI loading is delegated to Wevra
- **WHEN** a host app exposes its ASGI application
- **THEN** the app entry point delegates common loading and configuration-error reporting to Wevra
- **AND** the app entry point contains only app-factory import and the Wevra loader call
