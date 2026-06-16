## Why

`wybra.web` is becoming the place where unrelated web-adjacent concerns land:
HTML rendering, route setup, context, forms, CSRF, error handling, security
headers, template discovery, static asset serving, and static asset export.

Static assets are related to web delivery, but they are not the same concern as
HTML rendering or request/view handling. They have their own lifecycle:
configured module discovery, composed asset precedence, ASGI serving,
deployment suppression, collection/export, duplicate reporting, validation, and
future processing.

Keeping static assets inside `wybra.web` risks turning `wybra.web` into a
monolith that handles every HTTP-adjacent feature. Separating static asset
responsibilities into a dedicated module gives Wybra clearer boundaries:

- `wybra.web` owns rendering, request context, routes, forms, CSRF, security
  headers, and error handling.
- `wybra.static` owns static asset discovery, serving, collection, duplicate
  handling, validation, and static deployment controls.
- `wybra.media` owns writable runtime media, media catalogue records, media
  storage, and media URL/path resolution.

This also aligns with the planned `wybra-collect` command, which is static
asset infrastructure rather than rendering infrastructure.

## What Changes

- Add a first-class `wybra.static` module for static asset infrastructure.
- Move composed static asset serving out of `wybra.web.staticfiles` into
  `wybra.static`.
- Move static asset export/collection primitives out of `wybra.web` into
  `wybra.static`.
- Move static source discovery and duplicate/shadow handling that is specific
  to static assets into the static module boundary where practical.
- Keep route and template discovery in `wybra.web` unless they are directly
  static-specific.
- Keep static asset configuration under the existing `app.static` section
  unless a later design requires a Wybra-owned static section.
- Preserve `app.static.serve` as the app-side static serving suppression switch.
- Keep `static_mount_path` available to templates even when ASGI static serving
  is disabled, so deployments can serve static assets externally.
- Keep static asset URL generation independent of whether FastAPI sees the
  request. If nginx handles `/static/`, the app-side handler is irrelevant.
- Make `wybra.web` depend on the static module's public setup/helper APIs rather
  than carrying static implementation details internally.
- Leave `wybra.media` separate. Media is writable runtime data with catalogue
  records; static assets are packaged or collected deployment assets.

## Capabilities

### New Capabilities

- `static-assets`: Static asset source discovery, composed serving, export,
  duplicate/shadow reporting, validation support, and serving suppression.

### Modified Capabilities

- `site-startup-api`: Static serving should be configured through the static
  module during site setup rather than being embedded in `wybra.web`.
- `web-foundation`: Web setup should delegate static-specific behaviour to
  `wybra.static` and focus on rendering, request context, routes, forms, CSRF,
  security headers, and errors.
- `static-collection`: The future `wybra-collect` command should build on
  `wybra.static` rather than `wybra.web.staticfiles`.
- `environment-configuration`: Static serving/export settings remain explicit,
  including `app.static.serve`.

## Impact

- Reduces `wybra.web` surface area and avoids further monolith growth.
- Creates a clearer boundary for static collection/export work.
- Makes static serving controls explicit and reusable outside the HTML rendering
  module.
- Keeps media and static responsibilities separate: static files are deployment
  assets, while media files are runtime writable data.
- Requires updating imports and tests that currently reference
  `wybra.web.staticfiles`.
- Should not add new runtime dependencies.
