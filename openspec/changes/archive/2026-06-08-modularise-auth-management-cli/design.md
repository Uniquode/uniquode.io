## Context

The `wevra-authmgr` implementation has grown from a local user-administration
command into an auth-management CLI that also manages groups, scopes,
memberships, effective scopes, schema preflight checks, timestamp parsing,
password-source semantics, and multiple output formats. The implementation
currently lives behind one file of roughly 1,920 lines, which makes future
extended-authentication commands harder to add without coupling unrelated
concerns.

The accepted identity architecture places local identity administration tools
inside `wevra.auth` when they operate on the reusable identity model. The refactor
must preserve that package boundary and the current operator-facing CLI
contract.

The package now also has several Wevra-owned operator commands. Any CLI support
code that is not specific to auth management should be shared across those
commands instead of being hidden inside the auth CLI package. Database URL
resolution, database/session setup, project configuration loading, schema
preflight wiring, and common operator diagnostics are the main candidates to
keep aligned across `wevra-authmgr`, `wevra-migrate`, and future Wevra CLI
entrypoints.

## Goals / Non-Goals

**Goals:**

- Replace the current `wevra.auth.cli.identitymgr` implementation module with a
  `wevra.auth.cli.authmgr` package and make `wevra.auth.cli.authmgr:main` the
  project-script entry point.
- Split root CLI construction, user commands, group commands, scope commands,
  schema checks, output formatting, password-source handling, timestamp parsing,
  and command arguments into focused modules.
- Move concrete cross-command support code into shared Wevra CLI/tooling
  modules when the same concern is or will immediately be used by more than one
  Wevra operator command.
- Compose the command tree through explicit registration functions.
- Preserve existing command behaviour, help output, output formats, validation
  semantics, and exit statuses.
- Keep the refactor mechanical where possible and let the existing test suite
  confirm behavioural compatibility.

**Non-Goals:**

- Add automatic plugin discovery, entry-point scanning, filesystem scanning, or
  third-party command loading.
- Add new runtime dependencies or a dependency-injection framework.
- Create an abstract CLI framework for hypothetical future commands.
- Change operator-facing command syntax, service behaviour, persistence logic,
  schema requirements, output contracts, or password-source semantics.
- Introduce new extended-authentication commands in this refactor.
- Extract `wevra.auth` into a standalone distribution.

## Decisions

- Replace `src/wevra/auth/cli/identitymgr.py` with a package directory named
  `src/wevra/auth/cli/authmgr/`.
  - Rationale: `authmgr` matches the operator command name and describes the
    CLI's auth-management scope more clearly than the stale `identitymgr`
    internal module name.
  - Alternative considered: preserve `wevra.auth.cli.identitymgr` as an
    import-compatibility boundary. This product is unreleased, and preserving a
    stale internal name would add compatibility clutter before there are users
    to support.

- Export the supported public CLI surface from
  `wevra.auth.cli.authmgr.__init__`.
  - Rationale: the project script and direct public imports can use
    `wevra.auth.cli.authmgr:main`, while the package root remains limited to
    command construction, argument typing, password-source typing, program
    naming, and `main`.
  - Alternative considered: update `pyproject.toml` to point at
    `wevra.auth.cli.authmgr.cli:main`. That is workable but exposes an internal
    module path as the script boundary when the package root can own the public
    entry point.

- Keep auth-specific modules under `wevra.auth.cli.authmgr`, but move
  concrete reusable command support into shared Wevra tooling modules.
  - Rationale: database/config/session bootstrapping and common command
    diagnostics must remain consistent across Wevra-owned CLI scripts over the
    long term. If those helpers stay private to the auth manager, later commands
    will either duplicate them or depend on auth-specific internals.
  - Alternative considered: keep all moved code under the auth manager package
    for a smaller refactor. That is simpler locally but creates the wrong
    ownership boundary for code already needed by migration and other project
    commands.
  - Constraint: only extract concrete shared concerns. Auth-only helpers such
    as password input, identity timestamp parsing, and resource-specific output
    formatting should remain in the auth CLI package unless another command has
    an immediate use for them.

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

- Import compatibility risk -> Update direct public imports from the old
  `wevra.auth.cli.identitymgr` module to `wevra.auth.cli.authmgr`, import
  private helpers directly from their defining modules in tests, and run the
  full test suite.
- Circular import risk -> Keep shared dataclasses and helper APIs in low-level
  modules that do not import resource registration modules.
- Over-fragmentation risk -> Split by existing responsibilities only; avoid
  introducing extra abstraction layers until repeated use demands them.
- Shared-module overreach -> Share concrete cross-command concerns such as
  database/config/session setup, but do not create a generic CLI framework or
  move auth-specific helpers into global modules.
- Command registration drift -> Add focused tests that compare the command tree
  and representative command behaviour before and after the split.
- Future extension pressure -> Use explicit registration now and defer automatic
  discovery until a separate change defines plugin requirements.

## Migration Plan

1. Create the `wevra.auth.cli.authmgr` package structure and move the current
   module contents into focused modules.
2. Identify code that belongs in shared Wevra CLI/tooling modules before moving
   helpers into auth-specific modules.
3. Export only the supported public CLI surface from `__init__.py`.
4. Update `pyproject.toml` so `wevra-authmgr` resolves to
   `wevra.auth.cli.authmgr:main`.
5. Run focused auth-management CLI tests during each split step.
6. Run linting, formatting, type checking, the full test suite, and strict
   OpenSpec validation before handoff.

Rollback is straightforward because this is a structural refactor: restore the
single module and the previous imports if the package split or tests show
unacceptable risk.

## Open Questions

- Should future extended-authentication command modules register under the same
  explicit registration boundary, or should a later OpenSpec change introduce a
  narrower extension registry for those operations?
