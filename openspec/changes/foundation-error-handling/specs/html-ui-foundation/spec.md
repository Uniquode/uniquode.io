## ADDED Requirements

### Requirement: Error handling is explicit across route surfaces
The system SHALL provide explicit error-handling behaviour for page, partial, and
API route surfaces rather than relying on framework defaults.

#### Scenario: Page route `404` renders an HTML error page
- **WHEN** a browser requests a missing page route
- **THEN** the application returns an HTML `404` response rendered through the
  shared error-template foundation

#### Scenario: Page route `500` renders an HTML error page
- **WHEN** an unhandled server error occurs while serving a page route
- **THEN** the application returns an HTML `500` response rendered through the
  shared error-template foundation

#### Scenario: API route errors remain machine-oriented regardless of `Accept`
- **WHEN** a client requests an API route and the request fails
- **THEN** the application returns a machine-oriented error response rather than a
  template-rendered HTML page, even if the caller sends `Accept: application/json`
  or other browser-like headers

#### Scenario: Partial-route errors remain fragment-compatible
- **WHEN** a request intended for a partial or `htmx` fragment fails
- **THEN** the application returns an HTML error response that remains compatible
  with fragment-oriented clients rather than replacing the interaction with an
  unrelated full-page shell

### Requirement: Known and non-standard HTTP status codes have defined fallback behaviour
The system SHALL define fallback behaviour for both known HTTP status codes and
non-standard or application-specific termination-style status codes.

#### Scenario: Known HTTP status code uses generic fallback behaviour
- **WHEN** a request fails with a known HTTP status code that does not yet have a
  bespoke handler
- **THEN** the application uses a generic fallback representation that matches the
  current route surface rather than failing back to inconsistent framework defaults

#### Scenario: Non-standard termination-style status code bypasses generic rendering
- **WHEN** application policy selects a non-standard or termination-style status code
  such as `444`
- **THEN** the application bypasses generic HTML and JSON error rendering and uses
  the explicit empty-body or termination-style policy for that response path
