## Why

The current `web-foundation` implementation established templates, route surfaces,
theming, and partial rendering, but it did not establish an explicit error-handling
contract. Today the runtime falls back to framework defaults:

- missing routes return JSON `404` responses;
- `HTTPException` on API routes returns JSON;
- unhandled server errors fall back to plain-text `500` responses;
- the repository contains an HTML error template, but it is not wired into the app.

Error handling is foundational for any web service. The application needs an
explicit cross-surface policy for browser page requests, `htmx` partial requests,
and machine-oriented API requests before more feature work builds on top of the
current shell.

## What Changes

- Define foundational error-handling requirements under `html-ui-foundation`.
- Require explicit handling for common HTTP errors, including `404` and `500`,
  with generic fallback behaviour for other known HTTP status codes.
- Define route-surface-aware error representation so page routes, partial routes,
  and API routes do not leak the wrong response format to callers.
- Define a safe fallback policy for non-standard or application-specific status
  codes such as `444`, including connection-termination or empty-body style
  responses where that policy is explicitly selected.

## Capabilities

### Modified Capabilities
- `html-ui-foundation`: Extend the HTML-first UI foundation to include explicit
  error-handling rules for page, partial, and API surfaces, plus generic known-code
  fallback behaviour and handling expectations for non-standard termination-style
  status codes.

## Impact

- Affected code: application factory, exception handling, render helpers, and route
  surface policies.
- Affected tests: page, partial, and API error-path coverage, including content
  negotiation and unhandled-server-error behaviour.
- Affected specs: `html-ui-foundation`.
