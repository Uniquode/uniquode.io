## Context

The current repository already distinguishes page, partial, and API route surfaces,
but it does not yet distinguish their error behaviour. Runtime defaults are still
visible:

- browser misses currently receive framework JSON `404` responses unless a route
  handles the failure itself;
- API callers generally receive JSON for `HTTPException`, but unhandled server
  errors still degrade to plain text;
- the repository has an HTML error template, but no registered exception-handling
  policy uses it.

That leaves a gap in the web foundation. Error handling is not feature-local; it is
part of the baseline response contract for every later surface.

## Goals / Non-Goals

**Goals:**

- Define explicit `404` and `500` handling for browser-facing HTML page requests.
- Define explicit machine-oriented error handling for API routes, including
  unhandled `500` responses.
- Keep partial-route errors compatible with fragment-oriented clients rather than
  replacing the whole page shell unexpectedly.
- Provide generic fallback handling for other known HTTP status codes without
  requiring a bespoke template or serializer for each one.
- Define a safe policy for non-standard or application-specific status codes such
  as `444`, where the application may want to terminate quickly or emit no body.

**Non-Goals:**

- Finalise every future error payload shape for every domain-specific API.
- Add branded or deeply customised copy for every individual error page.
- Implement transport-level connection control beyond what the ASGI stack can
  actually support.

## Decisions

### 1. Route surface is the primary error-format selector

Error representation should be selected from the route surface first, not from
best-effort `Accept` guessing alone.

- Page routes should return full HTML error pages.
- Partial routes should return fragment-compatible HTML error responses.
- API routes should return machine-oriented responses.

`Accept` headers can refine behaviour where needed, but an API route should not
accidentally render an HTML error page just because a caller sends a browser-like
header set.

### 2. `404` and `500` are mandatory foundation cases

The application should explicitly handle `404 Not Found` and `500 Internal Server
Error` for all route surfaces.

These are the minimum operational requirements for the HTML-first shell and the API
surface. They should not be left to inconsistent framework defaults.

### 3. Known HTTP status codes should have generic fallback behaviour

The error system should not require one bespoke handler per status code before the
application can respond coherently. Common known codes such as `400`, `401`, `403`,
`404`, `405`, `409`, `422`, `429`, and `500` should be able to use a generic
surface-appropriate fallback.

That means:

- HTML page requests can render a base error template with status-specific heading
  and detail text.
- Partial requests can render a fragment-safe error block.
- API requests can return a machine-oriented status/error payload.

### 4. Non-standard or termination-style status codes need an explicit bypass path

The foundation should not assume every application-level error wants a conventional
HTML or JSON body. Non-standard or application-specific codes such as `444` are
useful when the application wants to terminate quickly or provide no response body.

Because exact transport semantics depend on the ASGI server and deployment stack,
the application-level contract should be:

- non-standard codes must not crash the error renderer;
- they may bypass generic HTML/JSON body rendering when the selected policy is an
  empty-body or termination-style response;
- the chosen behaviour must still be explicit and testable.

### 5. Foundation validation and tests should cover error-path behaviour

This slice should be verified through focused tests rather than assumed from the
framework defaults. The foundation should prove:

- HTML `404` and `500` rendering;
- API `404` and `500` machine-oriented responses;
- partial-route error behaviour;
- generic fallback handling for known codes;
- non-standard-code bypass behaviour.

## Risks / Trade-offs

- `Route-surface-first error handling may feel stricter than pure Accept negotiation`
  → This is intentional. It avoids API routes accidentally rendering HTML and keeps
  the foundation coherent.
- `Non-standard code handling may be constrained by ASGI/server behaviour`
  → The spec should define the application contract in terms of empty-body or
  termination-style policy rather than overpromising wire-level behaviour the stack
  cannot guarantee.
- `Generic fallback copy may be plain at first`
  → That is acceptable at foundation level; correctness and surface consistency are
  more important than polished bespoke wording at this stage.

## Migration Plan

1. Register explicit exception-handling hooks in the application shell.
2. Separate HTML page, partial, and API error rendering/serialization paths.
3. Add mandatory `404` and `500` coverage and generic handling for other known
   HTTP status codes.
4. Add explicit handling for non-standard termination-style codes such as `444`.
5. Add focused tests for all supported error surfaces and fallback modes.
