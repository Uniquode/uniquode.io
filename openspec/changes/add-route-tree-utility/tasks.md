## 1. Inspection Model

- [ ] 1.1 Add route-inspection data structures for route records, route tree
  nodes, endpoint shape, route origin, warnings, and problem records.
- [ ] 1.2 Implement installed FastAPI/Starlette app traversal for HTTP routes,
  websocket routes, mounted applications, and static mounts.
- [ ] 1.3 Add tests for deterministic route-record ordering across mixed
  route kinds.
- [ ] 1.4 Add best-effort endpoint identifier extraction using module and
  qualified function names.
- [ ] 1.5 Build both a flattened route-record list and a hierarchical route
  tree model from the installed application graph.

## 2. Wevra Origin Metadata

- [ ] 2.1 Record configured module name, router label, include prefix, route
  name, installed path, and installed methods during Wevra router registration.
- [ ] 2.2 Join installed route records to Wevra origin metadata without
  changing runtime dispatch behaviour.
- [ ] 2.3 Add tests showing configured module routes include origin metadata
  and plain FastAPI routes remain inspectable without it.

## 3. Endpoint Shape Detection

- [ ] 3.1 Infer route-surface shape from available runtime metadata, including
  API, page, partial, static, mount, and unknown surfaces.
- [ ] 3.2 Detect body and form input for FastAPI `APIRoute` endpoints where
  FastAPI exposes that metadata.
- [ ] 3.3 Detect path parameter names and available parameter metadata.
- [ ] 3.4 Report explicit template metadata when a supported endpoint or route
  metadata convention provides it.
- [ ] 3.5 Add tests proving template names are not inferred by parsing handler
  source code.

## 4. Smoke Checks

- [ ] 4.1 Detect duplicate non-blank route names in the installed route tree.
- [ ] 4.2 Detect duplicate explicit HTTP method and path combinations after
  normalising framework-generated details such as implicit `HEAD` handling.
- [ ] 4.3 Detect malformed route records that cannot expose a coherent path or
  method set.
- [ ] 4.4 Detect route-origin metadata that does not match the installed route
  graph coherently.
- [ ] 4.5 Add tests for failing and passing route smoke-check outcomes.

## 5. Output And CLI

- [ ] 5.1 Add succinct text rendering with one compact line per route or mount.
- [ ] 5.2 Add expanded graph-like text rendering that shows path hierarchy,
  mounts, route leaves, origin, and endpoint shape.
- [ ] 5.3 Add Mermaid diagram rendering with deterministic node IDs and escaped
  labels.
- [ ] 5.4 Add JSON output that includes structured tree nodes, flattened route
  records, warnings, and problems.
- [ ] 5.5 Add a Click-based route-inspection command that loads the configured
  host ASGI app target through Wevra project-tool metadata.
- [ ] 5.6 Add command options for succinct, graph-like, Mermaid, JSON, and
  check mode.
- [ ] 5.7 Add CLI tests for successful output, configuration failures, and
  non-zero check failures.

## 6. Host Integration And Documentation

- [ ] 6.1 Expose the route-inspection command through the application project
  scripts without adding a runtime dependency.
- [ ] 6.2 Document local usage for succinct, graph-like, Mermaid, and JSON
  route-tree representations.
- [ ] 6.3 Document explicit route smoke checking.
- [ ] 6.4 Document that the existing validation command remains broad project
  validation and does not render the route tree as its main concern.

## 7. Final Validation

- [ ] 7.1 Run focused Wevra route-inspection tests.
- [ ] 7.2 Run the application test suite that covers project-script wiring.
- [ ] 7.3 Run Ruff format and lint checks for affected Wevra and app files.
- [ ] 7.4 Run `ty check src` for affected Python projects.
- [ ] 7.5 Run `openspec validate add-route-tree-utility --strict`.
- [ ] 7.6 Run strict main spec validation.
- [ ] 7.7 Run `git diff --check`.
