## Why

The application can now compose routes from module-owned FastAPI routers, but
developers and reviewers do not have a compact way to see the entire final
installed route tree. A separate route-inspection utility should make that tree
visible in multiple representations and provide a focused smoke test for route
collisions and endpoint shape, without making route validation the main concern
of the existing validation command.

## What Changes

- Add a route-tree inspection utility that loads the host application's
  configured runtime and reports the entire installed route tree.
- Provide a succinct output format for quick review, with one compact line per
  route or mount.
- Provide an expanded graph-like text format that shows the route tree by path
  hierarchy, mounts, methods, route names, module/router origin, and inferred
  endpoint shape.
- Provide a Mermaid diagram output mode so the installed route tree can be
  pasted into documentation, review notes, or design discussions.
- Provide a JSON output mode for tests, review automation, or future
  documentation generation.
- Add a check mode that exits non-zero when it detects route-surface problems
  such as endpoint-name collisions, method/path collisions, malformed route
  metadata, or installed routes that cannot be represented coherently.
- Inspect the final installed FastAPI/Starlette route graph as the primary
  source of truth, with optional composition metadata from Wevra route
  registration where available.
- Classify endpoint shape using runtime route metadata where possible,
  including API versus HTML, template/page versus partial, form/body input,
  path parameters, dependencies, and mounted/static routes.
- Treat template-name discovery as explicit metadata or best-effort inference;
  do not parse handler source code to discover templates.
- Keep the existing validation command focused on broad project structure.
  Route-tree checks may share lower-level route-inspection helpers, but they
  are exposed through the prefixed `wevra-routes` command or utility surface.
- Do not add a runtime dependency.

## Capabilities

### New Capabilities

- `route-inspection`: Provides route-tree representations and smoke checks for
  configured FastAPI applications composed through Wevra.

### Modified Capabilities

- `application-infrastructure`: Move reusable Wevra operator commands to
  prefixed package-owned console scripts so host applications do not need to
  re-declare bare command names.

## Impact

- Affected code is expected to include Wevra route composition metadata,
  route-inspection helpers, output renderers, a CLI entry point or tool command,
  prefixed Wevra package script wiring, tests around route-tree output/check
  behaviour, and documentation for using the utility in review or local
  smoke-test workflows.
- The utility may be consumed from the `uniquode.io` workspace while its
  implementation belongs primarily in the reusable Wevra package.
- Existing application runtime behaviour should not change.
