## Context

The route refactor moved Wevra and the host application to FastAPI-native
`APIRouter` composition. Configured modules now expose labelled routers through
`module_routers`, and the host application decides where each router is mounted
through route-prefix configuration.

Composition validation already checks important structural issues while routers
are being loaded. That is useful, but it does not give reviewers and developers
a picture of the final installed application route tree. The final FastAPI app
can also contain static routes, mounted routes, sub-applications, and host-owned
additions that are visible only after application construction.

The new utility should therefore inspect the installed FastAPI/Starlette route
graph. It can reuse Wevra project-tool metadata to load the host application
from the same configured ASGI target used by local development commands.

## Goals / Non-Goals

**Goals:**

- Provide a route-tree utility that shows the entire final installed route
  tree.
- Support four output representations: succinct text, expanded graph-like text,
  Mermaid diagram text, and JSON.
- Make the output useful as both a review aid and a focused route smoke test.
- Detect endpoint-name collisions and method/path collisions in the installed
  route graph.
- Report endpoint shape where the runtime route graph exposes enough metadata:
  API/HTML/static/mount surface, methods, path parameters, request body or form
  input, dependencies, response media type, and explicit template metadata.
- Preserve JSON as the machine-readable output format for tests and future
  documentation generation.
- Keep route inspection separate from the existing validation command.
- Avoid adding runtime dependencies.

**Non-Goals:**

- Do not replace FastAPI/Starlette routing, OpenAPI generation, or dependency
  analysis.
- Do not make broad project validation depend on route-tree output.
- Do not parse endpoint source code to discover template names or handler
  intent.
- Do not require every route to use Wevra metadata; non-Wevra routes must still
  be listed with best-effort shape information.
- Do not change the runtime route behaviour of the application.

## Decisions

### Inspect The Installed Application Route Graph

The primary input is the constructed FastAPI/Starlette application object, not
the pre-installation `module_routers` mapping.

The utility should load the host project using existing Wevra project-tool
metadata and import the configured ASGI app target. The current metadata name is
`runserver_app`; the implementation can reuse that option initially because it
already identifies the canonical application object. If a broader tool-facing
name is introduced later, it should be an alias or migration from the same
configured target rather than a second competing setting.

Alternative considered: inspect only `load_configured_module_routes(settings)`.
That is useful for explaining Wevra composition, but it misses host-added
routes, static mounts, and final route objects cloned by FastAPI during
inclusion. It should remain optional supporting metadata, not the source of
truth.

### Attach Optional Wevra Route Origin Metadata During Composition

FastAPI route inclusion produces final route objects on the app. To explain
where a route came from, Wevra should record origin metadata when it includes
configured module routers. The metadata should be lightweight and observational,
for example:

- configured module name;
- router label;
- configured include prefix;
- route name, path, and methods as installed.

The metadata should live in app state or on route-extra metadata in a way that
does not affect dispatch. The route inspector can then join installed routes to
origin metadata, while plain FastAPI routes remain inspectable without origin
data.

Alternative considered: reconstruct origin after the fact by matching endpoint
module names or path prefixes. That is brittle and will be wrong for shared
handlers, included routers, and root-mounted module surfaces.

### Represent Inspection As Structured Tree Records

Route inspection should produce a structured model before rendering human or
JSON output. The model should preserve both a flattened route-record list and a
path/mount hierarchy so different output formats can render the same
inspection. Each record should include:

- route kind: HTTP route, websocket route, mount, static mount, or unknown;
- methods, path, name, endpoint import path or qualified name;
- origin metadata when available;
- path parameters and converter/type information when available;
- response media type or response class where available;
- input shape, including form/body presence when FastAPI exposes it;
- route-surface classification such as API, page, partial, static, mount, or
  unknown;
- explicit template metadata when an endpoint or route helper provides it;
- warnings for incomplete or ambiguous classification.

This keeps formatting separate from inspection and makes check mode operate on
the same data that JSON output exposes.

### Provide Dedicated Output Renderers

The utility should provide four output renderers over the same structured route
tree:

- `succinct`: compact one-line route or mount records for quick scanning;
- `graph`: expanded graph-like text that shows path hierarchy, mounts, route
  methods, names, origin, and endpoint shape;
- `mermaid`: Mermaid flowchart text that represents the installed route tree as
  diagram nodes and edges;
- `json`: structured route tree, route records, warnings, and detected
  problems for machine consumption.

The succinct format should be the default because it is useful in terminals and
review comments. The graph-like format should be optimised for humans who want
to understand path hierarchy and mounted subtrees. The Mermaid format should
produce plain text only; rendering the diagram is left to Mermaid-aware tools,
so no diagram-rendering dependency is needed.

Alternative considered: provide only JSON and let callers build their own
renderers. That would be flexible, but it would not satisfy the main review use
case: seeing the route tree directly without extra tooling.

### Keep Shape Classification Conservative

The utility should classify what can be known from runtime metadata and mark the
rest as `unknown` or `not declared`.

API/page/partial detection can use a combination of response media type,
Wevra route-surface metadata, configured route prefixes, and known constants
such as the API and partial path prefixes. Form/body input can be inferred from
FastAPI `APIRoute` body/dependency metadata. Path parameters can be read from
the route path format and FastAPI route metadata.

Template names require explicit metadata from a Wevra helper, endpoint
attribute, decorator, or future route metadata convention. The inspector must
not parse handler source code or attempt to infer template paths from arbitrary
function bodies.

Alternative considered: use AST/source inspection to find `render_page(...)`
calls. That would be fragile, would miss dynamic rendering, and would fail for
packaged or optimised code.

### Separate Representation From Check Behaviour

The default command should render the succinct route-tree representation for
humans. The graph-like and Mermaid modes should be representation-only unless
combined with check mode. JSON should emit the same records and problems as
structured data. A check mode should exit non-zero when route problems are
detected.

Initial problems should include:

- duplicate non-blank route names;
- duplicate HTTP method and concrete path pairs after normalisation;
- malformed route records that cannot expose a coherent path or method set;
- route-origin metadata that points at no installed route or multiple
  incompatible installed routes.

The check mode should normalise framework-generated details carefully. For
example, implicit `HEAD` support and framework-owned `OPTIONS` handling should
not create false collisions unless they are installed as explicit routes.

### Keep Validation Separate

The existing validation command may share lower-level route-inspection helpers
later, but it should not run the route-tree smoke test as part of its default
web validation target. A developer or CI job that wants route smoke testing
should invoke the new utility explicitly, for example through a project script
such as `routes --check`.

## Risks / Trade-offs

- Importing the ASGI app can run application startup wiring or import-time side
  effects. Mitigation: load the same target used by `runserver`, document that
  the utility imports but does not serve the app, and keep tests around app
  construction.
- FastAPI internals used for body/form/dependency shape can change. Mitigation:
  isolate FastAPI-specific inspection behind small helper functions and treat
  unavailable metadata as unknown rather than fatal.
- Shape output may look incomplete until endpoints declare explicit metadata.
  Mitigation: make unknown fields visible and introduce explicit Wevra metadata
  only when requirements need stronger guarantees.
- Duplicate detection on mounted apps can be incomplete without recursively
  walking mounts. Mitigation: support recursive inspection of FastAPI/Starlette
  mounts where possible and clearly label opaque mounts in all representations.
- Mermaid node labels can break diagrams if route names or paths are not escaped
  correctly. Mitigation: centralise Mermaid ID generation and label escaping,
  with tests for punctuation, path parameters, and repeated labels.
- Human output can become noisy on large applications. Mitigation: make the
  succinct format compact, use the graph-like format when hierarchy matters,
  and keep JSON as the stable machine contract.

## Migration Plan

1. Add route-inspection helpers and tests without changing runtime dispatch.
2. Record optional Wevra route-origin metadata during router registration.
3. Add the CLI/tool command, output renderers, and host project script wiring.
4. Document local review and CI smoke-test usage.
5. Roll back by removing the project script and inspector helpers; application
   runtime behaviour is not part of the change.

## Open Questions

None for the first implementation. A future change can decide whether Wevra
should provide a first-class decorator or route-helper metadata API for template
names and richer page/partial classification.
