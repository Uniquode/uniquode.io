## Context

`identitymgr` started as a local user-management command, so short top-level
actions such as `identitymgr create` and `identitymgr list` were initially
reasonable. The command now also manages groups and scopes, which makes the
top-level command tree inconsistent: groups and scopes are resource-prefixed,
while users still occupy action names at the root.

This change is intentionally pre-release. We should choose the canonical
operator interface now and avoid adding compatibility aliases that would create
unnecessary support obligations.

## Goals / Non-Goals

**Goals:**

- Make `identitymgr user ...` the required namespace for all user operations.
- Preserve existing user operation names, options, positional arguments, output
  formats, validation, and service behaviour under the new namespace.
- Keep `identitymgr group ...` and `identitymgr scope ...` unchanged.
- Reject old top-level user action commands rather than supporting aliases.
- Update documentation and tests to describe the resource-oriented command tree.

**Non-Goals:**

- Redesign group or scope command syntax.
- Change user-management service behaviour, persistence, schema checks,
  password policy, password prompting, output records, or exit-code semantics.
- Add legacy compatibility, redirects, or deprecation warnings for the old
  top-level user commands.

## Decisions

- Add a Click `user` group under `identitymgr_command`.
  - Rationale: Click already models `scope` as a subcommand group, and a user
    group makes the top-level help resource-oriented.
  - Alternative considered: keep the short top-level commands. This preserves
    brevity but keeps the CLI asymmetric as additional identity resources are
    added.

- Move the existing user command callbacks under the `user` group without
  changing their internal command identifiers.
  - Rationale: `_run_identitymgr` can continue dispatching `"create"`,
    `"update"`, `"delete"`, `"deactivate"`, `"list"`, and `"password"` to the
    same service calls, minimising implementation risk.
  - Alternative considered: rename internal command identifiers to
    `"user-create"` and similar. That is more explicit internally but creates
    unnecessary churn for no operator-visible benefit.

- Do not register compatibility aliases for top-level user commands.
  - Rationale: the product has not been released, so supporting legacy commands
    would add artificial surface area and test burden without protecting real
    users.
  - Alternative considered: keep hidden aliases or emit deprecation warnings.
    That would be appropriate after a release, but not before one.

- Keep group membership options on user commands unchanged.
  - Rationale: `identitymgr user create --group ...` and
    `identitymgr user update --add-group ...` remain clear and continue to use
    existing group target resolution.
  - Alternative considered: moving user membership edits under `group` only.
    That would remove useful user-centric workflows and is outside this
    structural cleanup.

## Risks / Trade-offs

- Existing local scripts using the old development command names will fail.
  - Mitigation: this is pre-release; update repository documentation, examples,
    and tests in the same change.

- Root help becomes less action-oriented and one command longer for user tasks.
  - Mitigation: the resource-oriented structure is clearer as the CLI grows and
    aligns users with groups and scopes.

- Some tests may encode old usage strings deeply.
  - Mitigation: update CLI tests to assert the new canonical help and command
    paths, including negative coverage that old top-level commands are absent.
