## Why

Static assets should be deliverable efficiently outside the ASGI application when desired. Collecting the exact static files a configured Wybra site would serve allows deployments to hand static delivery to nginx or another front end that can use efficient file-serving primitives instead of routing those requests through Starlette/FastAPI.

## What Changes

- Add a `wybra-collect` script/command that reads the configured site modules and collects every static file that would be served by Wybra static file handlers.
- Copy collected files to a destination selected by Wybra defaults, app configuration, or CLI override.
- Preserve copied file metadata, including modification times, so downstream servers and caches can use stable filesystem metadata.
- Respect the same static-source and override semantics used by runtime static handling, so the collected tree matches what Wybra would serve.
- Allow developers to override runtime static handling to serve files from the collected root, or add module options where appropriate, such as in `wybra.auth`, to point runtime/static URLs at collected assets.
- Support direct serving from nginx or similar web servers for static files that would otherwise be served by the ASGI app.
- Add a processor extension point so collection can optionally transform or generate assets through configured external processors.
- Processor examples include Sass/SCSS compilation to CSS, CSS minification, and JavaScript minification.

## Capabilities

### New Capabilities

- `static-asset-collection`: Collect configured module static assets into a deployable filesystem tree, preserving runtime static resolution semantics and allowing configured processing.

### Modified Capabilities

- `web-foundation`: Static asset delivery gains an offline collection path aligned with the runtime static files served by Wybra web.

## Impact

- Adds a `wybra-collect` CLI/tooling entry point for static asset collection.
- Adds configuration for static collection destination and optional processors.
- Touches Wybra web/static discovery and static serving behaviour to ensure collection and runtime serving use the same source model.
- May affect app deployment documentation by recommending collected static serving through nginx or equivalent front-end servers.
- Does not require host apps to manually copy module static files or know Wybra internals.
