## MODIFIED Requirements

### Requirement: HTML route surfaces are explicit
The system SHALL keep page routes, partial routes, and API routes as distinct
route surfaces for rendering, validation, and exception-response selection,
without requiring modules to declare separate route tables for each surface.

#### Scenario: Page route renders a full template
- **WHEN** a browser requests a page route
- **THEN** the handler returns a full HTML page response rendered from the
  template system or another valid page response

#### Scenario: Partial route renders a fragment
- **WHEN** a browser requests a partial route intended for `htmx`
- **THEN** the handler returns an HTML fragment response rather than a full page
  shell

#### Scenario: API route stays machine-oriented
- **WHEN** a client requests an API route
- **THEN** the handler returns a machine-oriented response rather than a
  template-rendered HTML page

#### Scenario: Route surface is route metadata
- **WHEN** a module declares routes
- **THEN** page, partial, and API surface information is declared or inferred as
  route metadata rather than by placing routes into separate top-level route
  buckets

### Requirement: HTML requests use a dispatcher protocol
The system SHALL provide an internal request-dispatch layer under FastAPI for
module-owned route handlers, with route definitions composed from explicitly
installed application modules.

#### Scenario: Module routes declare a namespace and route map
- **WHEN** a configured module exposes its route surface
- **THEN** it declares a module namespace and a mapping of route keys to route
  targets rather than requiring separate page-route, partial-route, and submit
  route collections

#### Scenario: Route key defines default path and name
- **WHEN** a module declares a route key without an explicit path or route name
- **THEN** the route key is used to derive the relative route path and the
  reverse-route name within the module namespace

#### Scenario: Application mount prefixes relative module routes
- **WHEN** the application configures a route prefix for a module
- **THEN** module-relative route paths are mounted beneath that prefix

#### Scenario: Absolute route bypasses module mount
- **WHEN** a module route declares an absolute path
- **THEN** the route is registered at that absolute path and does not receive
  the module mount prefix

#### Scenario: Module-root route is supported
- **WHEN** a module route declares an empty relative path and the application
  configures a route prefix for that module
- **THEN** the route is mounted at the module prefix itself

#### Scenario: Route targets are constructed lazily
- **WHEN** a module declares a route target as a class or factory
- **THEN** the route declaration stores the target without constructing it
  during module import

#### Scenario: Class view dispatches by HTTP method
- **WHEN** a request reaches a class-based view
- **THEN** the base view dispatch validates the request method against the
  view's supported method list and calls the corresponding method handler

#### Scenario: Function view receives request
- **WHEN** a route target is a plain function
- **THEN** the dispatcher calls it with the request as the first required
  argument and allows the function to decide how to handle the request method

#### Scenario: Method helpers are shared
- **WHEN** class-based views or function views need to validate HTTP methods
- **THEN** they can use shared `wevra.web` helpers to determine whether the
  request method is handled and to return a method-not-allowed response

#### Scenario: Reverse URL names are logical
- **WHEN** templates or handlers link to a module route
- **THEN** they use the generated reverse-route name based on module namespace
  and route key rather than hard-coding the mounted URL path

### Requirement: Error handling is explicit across route surfaces
The system SHALL provide explicit error-handling behaviour for page, partial,
and API route surfaces rather than relying on framework defaults.

#### Scenario: Dispatcher handles view exceptions
- **WHEN** a class-based view or function route handler raises an exception
- **THEN** the dispatcher passes the exception to a global `wevra.web`
  exception-handling boundary before returning a response

#### Scenario: Page route `404` renders an HTML error page
- **WHEN** a browser requests a missing page route or a page route raises a
  not-found exception
- **THEN** the application returns an HTML `404` response rendered through the
  shared error-template foundation

#### Scenario: Page route `500` renders an HTML error page
- **WHEN** an unhandled server error occurs while serving a page route
- **THEN** the application returns an HTML `500` response rendered through the
  shared error-template foundation

#### Scenario: API route errors remain machine-oriented regardless of `Accept`
- **WHEN** a client requests an API route and the request fails
- **THEN** the application returns a machine-oriented error response rather than
  a template-rendered HTML page, even if the caller sends `Accept: text/html`
  or other browser-like headers

#### Scenario: Partial-route errors remain fragment-compatible
- **WHEN** a request intended for a partial or `htmx` fragment fails
- **THEN** the application returns an HTML error response that remains
  compatible with fragment-oriented clients rather than replacing the
  interaction with an unrelated full page

#### Scenario: Unsupported methods return `405`
- **WHEN** a route handler does not support the request method
- **THEN** the response status is `405 Method Not Allowed` and the `Allow`
  header lists the supported methods

#### Scenario: Exception handlers are extensible without host imports
- **WHEN** a framework module or host application needs specialised exception
  mapping
- **THEN** it can register exception handlers with the web dispatch boundary
  without `wevra.web` importing the host application package
