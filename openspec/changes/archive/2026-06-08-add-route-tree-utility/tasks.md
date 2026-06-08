## 1. Inspection Model

- [x] 1.1 Add route-inspection data structures for route records, route tree
  nodes, endpoint shape, route origin, warnings, and problem records.
- [x] 1.2 Implement installed FastAPI/Starlette app traversal for HTTP routes,
  websocket routes, mounted applications, and static mounts.
- [x] 1.3 Add tests for deterministic route-record ordering across mixed
  route kinds.
- [x] 1.4 Add best-effort endpoint identifier extraction using module and
  qualified function names.
- [x] 1.5 Build both a flattened route-record list and a hierarchical route
  tree model from the installed application graph.

## 2. Wevra Origin Metadata

- [x] 2.1 Record configured module name, router label, include prefix, route
  name, installed path, and installed methods during Wevra router registration.
- [x] 2.2 Join installed route records to Wevra origin metadata without
  changing runtime dispatch behaviour.
- [x] 2.3 Add tests showing configured module routes include origin metadata
  and plain FastAPI routes remain inspectable without it.

## 3. Endpoint Shape Detection

- [x] 3.1 Infer route-surface shape from available runtime metadata, including
  API, page, partial, static, mount, and unknown surfaces.
- [x] 3.2 Detect body and form input for FastAPI `APIRoute` endpoints where
  FastAPI exposes that metadata.
- [x] 3.3 Detect path parameter names and available parameter metadata.
- [x] 3.4 Report explicit template metadata when a supported endpoint or route
  metadata convention provides it.
- [x] 3.5 Add tests proving template names are not inferred by parsing handler
  source code.

## 4. Smoke Checks

- [x] 4.1 Detect duplicate non-blank route names in the installed route tree.
- [x] 4.2 Detect duplicate explicit HTTP method and path combinations after
  normalising framework-generated details such as implicit `HEAD` handling.
- [x] 4.3 Detect malformed route records that cannot expose a coherent path or
  method set.
- [x] 4.4 Detect route-origin metadata that does not match the installed route
  graph coherently.
- [x] 4.5 Add tests for failing and passing route smoke-check outcomes.

## 5. Output And CLI

- [x] 5.1 Add succinct text rendering with one compact line per route or mount.
- [x] 5.2 Add expanded graph-like text rendering that shows path hierarchy,
  mounts, route leaves, origin, and endpoint shape.
- [x] 5.3 Add Mermaid diagram rendering with deterministic node IDs and escaped
  labels.
- [x] 5.4 Add JSON output that includes structured tree nodes, flattened route
  records, warnings, and problems.
- [x] 5.5 Add a Click-based route-inspection command that loads the configured
  host ASGI app target through Wevra project-tool metadata.
- [x] 5.6 Add command options for succinct, graph-like, Mermaid, JSON, and
  check mode.
- [x] 5.7 Add CLI tests for successful output, configuration failures, and
  non-zero check failures.
- [x] 5.8 Add quiet check mode that suppresses route-tree output and reports
  route-surface problems through exit status.
- [x] 5.9 Add direct output format flags for succinct, graph-like, Mermaid,
  and JSON route-tree representations.
- [x] 5.10 Refine graph output into a visually connected compact route tree.
- [x] 5.11 Suppress repeated graph origin metadata when a route-tree group
  already establishes the same module-router origin.

## 6. Host Integration And Documentation

- [x] 6.1 Expose the route-inspection command through a prefixed Wevra package
  script without adding a runtime dependency.
- [x] 6.2 Move reusable Wevra operator command documentation to prefixed
  package-owned names: `wevra-runserver`, `wevra-migrate`, `wevra-routes`,
  `wevra-validate`, and `wevra-identitymgr`.
- [x] 6.3 Remove host application script declarations for Wevra-owned operator
  commands.
- [x] 6.4 Document local usage for succinct, graph-like, Mermaid, and JSON
  route-tree representations.
- [x] 6.5 Document explicit route smoke checking.
- [x] 6.6 Document that the existing validation command remains broad project
  validation and does not render the route tree as its main concern.

## 7. Final Validation

- [x] 7.1 Run focused Wevra route-inspection tests.
- [x] 7.2 Run the application test suite that covers project-script wiring.
- [x] 7.3 Run Ruff format and lint checks for affected Wevra and app files.
- [x] 7.4 Run `ty check src` for affected Python projects.
- [x] 7.5 Run `openspec validate add-route-tree-utility --strict`.
- [x] 7.6 Run strict main spec validation.
- [x] 7.7 Run `git diff --check`.
