## Context

`identitymgr` has grown from a local user-administration command into an
identity-management CLI that also manages groups, scopes, memberships,
effective scopes, schema preflight checks, timestamp parsing, password-source
semantics, and multiple output formats. The implementation currently lives in
one file of roughly 1,920 lines, which makes future extended-authentication
commands harder to add without coupling unrelated concerns.

The accepted identity architecture places local identity administration tools
inside `wevra.auth` when they operate on the reusable identity model. The refactor
must preserve that package boundary and the current operator-facing CLI
contract.

## Goals / Non-Goals

**Goals:**

- Convert `wevra.auth.cli.identitymgr` into a package while preserving
  `wevra.auth.cli.identitymgr:main` as the project-script entry point.
- Split root CLI construction, user commands, group commands, scope commands,
  schema checks, output formatting, password-source handling, timestamp parsing,
  and command arguments into focused modules.
- Compose the command tree through explicit registration functions.
- Preserve existing command behaviour, help output, output formats, validation
  semantics, and exit statuses.
- Keep the refactor mechanical where possible and let the existing test suite
  confirm behavioural compatibility.

**Non-Goals:**

- Add automatic plugin discovery, entry-point scanning, filesystem scanning, or
  third-party command loading.
- Add new runtime dependencies or a dependency-injection framework.
- Change operator-facing command syntax, service behaviour, persistence logic,
  schema requirements, output contracts, or password-source semantics.
- Introduce new extended-authentication commands in this refactor.
- Extract `wevra.auth` into a standalone distribution.

## Decisions

- Turn `src/wevra/auth/cli/identitymgr.py` into a package directory named
  `src/wevra/auth/cli/identitymgr/`.
  - Rationale: Python import resolution supports `wevra.auth.cli.identitymgr:main`
    from a package `__init__.py`, so the project script can remain stable while
    implementation modules are split.
  - Alternative considered: keep a shim module next to a differently named
    package. Python cannot have both `identitymgr.py` and `identitymgr/` as the
    same import target cleanly in one package, and a differently named package
    would make the public boundary less obvious.

- Export `main` from `wevra.auth.cli.identitymgr.__init__`.
  - Rationale: the project script and any direct imports can keep using
    `wevra.auth.cli.identitymgr:main`.
  - Alternative considered: update `pyproject.toml` to point at
    `wevra.auth.cli.identitymgr.cli:main`. That is workable but creates unnecessary
    project-script churn when the stable entry point can remain unchanged.

- Use explicit `register_*_commands(root_command)` functions for command
  composition.
  - Rationale: registration makes the extension points visible and testable
    while avoiding import-order surprises.
  - Alternative considered: automatic module discovery. That would make future
    extensibility more dynamic, but it introduces decisions about naming
    conflicts, import failures, command ordering, dependency loading, and plugin
    trust that are not required yet.

- Keep dispatcher identifiers stable during the split.
  - Rationale: existing service dispatch can remain the behavioural anchor while
    command registration moves into modules.
  - Alternative considered: redesign dispatcher identifiers around resource
    modules. That could be cleaner later but adds behavioural risk to a
    structural refactor.

- Keep group command parsing isolated until its command shape is redesigned.
  - Rationale: group commands currently use target-first parsing in places, and
    preserving that behaviour is more important than forcing the parser into the
    same shape as Click-native user and scope commands during this refactor.
  - Alternative considered: convert group commands fully to nested Click
    subcommands. That is a separate operator-interface change and should not be
    hidden inside the module split.

## Risks / Trade-offs

- Import compatibility risk -> Preserve `wevra.auth.cli.identitymgr:main`, export
  helpers intentionally where tests or supported code import them, and run the
  full test suite.
- Circular import risk -> Keep shared dataclasses and helper APIs in low-level
  modules that do not import resource registration modules.
- Over-fragmentation risk -> Split by existing responsibilities only; avoid
  introducing extra abstraction layers until repeated use demands them.
- Command registration drift -> Add focused tests that compare the command tree
  and representative command behaviour before and after the split.
- Future extension pressure -> Use explicit registration now and defer automatic
  discovery until a separate change defines plugin requirements.

## Migration Plan

1. Create the `wevra.auth.cli.identitymgr` package structure and move the current
   module contents into focused modules.
2. Export `main` and supported test-facing helpers from `__init__.py`.
3. Keep `pyproject.toml` unchanged unless implementation proves a stable
   `wevra.auth.cli.identitymgr:main` export is not viable.
4. Run focused auth-management CLI tests during each split step.
5. Run linting, formatting, type checking, the full test suite, and strict
   OpenSpec validation before handoff.

Rollback is straightforward because this is a structural refactor: restore the
single module and the previous imports if package import compatibility or tests
show unacceptable risk.

## Open Questions

- Which helper names imported directly by tests should be considered public
  package exports after the split?
- Should future extended-authentication command modules register under the same
  explicit registration boundary, or should a later OpenSpec change introduce a
  narrower extension registry for those operations?
