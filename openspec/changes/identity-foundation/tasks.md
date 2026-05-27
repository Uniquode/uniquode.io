## 1. `identity-refactor` Sub-Spec

- [x] 1.1 Add the `identity-refactor` sub-spec describing the structural package
  boundary.
- [x] 1.2 Promote the existing `uniquode.identity` implementation shape into the
  independent top-level `auth_ext` package.
- [x] 1.3 Ensure the top-level `auth_ext` package does not import `uniquode`,
  `uniquode.settings`, `uniquode.persistence`, templates, or application route
  modules.
- [x] 1.4 Keep `uniquode` as the host/web interface by adapting application
  settings into identity options and composing identity routes from the host.
- [x] 1.5 Preserve existing identity behaviour while changing structure; do not
  add new user lifecycle or authentication behaviour in this slice.
- [x] 1.6 Update imports, package metadata, and tests for the new dependency
  direction.
- [x] 1.7 Add an import-boundary test or equivalent validation that fails if the
  `auth_ext` package depends on `uniquode`.
- [x] 1.8 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate identity-foundation --strict`.

## 2. Deferred Identity Foundation Sub-Specs

- [ ] 2.1 Define the baseline local identity sub-spec after `identity-refactor`
  lands.
- [ ] 2.2 Define the persistent development database sub-spec for `UT-178`
  separately from the structural refactor.
- [ ] 2.3 Define advanced authentication sub-specs only after the reusable
  package boundary is stable.
