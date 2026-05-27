## 1. Error Handling Foundation

- [x] 1.1 Register explicit error-handling hooks in the application shell for page,
  partial, and API surfaces.
- [x] 1.2 Implement mandatory `404` and `500` handling across those surfaces.
- [x] 1.3 Add generic fallback handling for other known HTTP status codes so the
  application does not depend on one bespoke handler per status.
- [x] 1.4 Add an explicit bypass path for non-standard or termination-style status
  codes such as `444`, including empty-body handling where that policy is selected.

## 2. Verification

- [x] 2.1 Add focused tests for HTML page `404` and `500` responses.
- [x] 2.2 Add focused tests for API `404` and `500` responses, including
  machine-oriented behaviour regardless of browser-like `Accept` headers.
- [x] 2.3 Add focused tests for partial-route error behaviour.
- [x] 2.4 Add focused tests for generic known-code fallback and non-standard-code
  bypass behaviour.
