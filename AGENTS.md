# Agent Notes

Use OpenSpec. Before implementing, identify or create the relevant change and align work with its artifacts.

Use [openspec/adr](openspec/adr) as the source of truth for accepted
architecture and platform decisions. Update ADRs for any change that affects
the architecture or platform. ADR documents are authoritative decision records,
not summaries of implementation details.

Prefer small, requirement-driven changes. Do not add runtime dependencies or framework structure before a requirement needs them.

Use UK/AU spelling at all times, including documentation, comments, function names, class names, and variable names.

User/account operational timestamps in this application are Unix timestamp
floats by explicit requirement. Do not propose replacing them with
`DateTime`, integer timestamps, or database-native timestamp columns in code
review or implementation unless the user explicitly opens a new architecture
to accommodate that decision.

Never use `--no-gpg-sign` or `--no-verify` with Git commands. If a commit fails,
stop and inform the user.

If `.guide.yaml` exists, treat it as current local project state.
Read `.todo/context.md` at session start when present. Update it at meaningful milestones.

Use `.agents/skills` or `~/.agents/skills` on demand.
Use `.agents/steering/` or `~/.agents/steering` on demand; start with
`.agents/steering/README.md` when unsure which file applies.

# Linear, GitHub And OpenSpec

Use Linear issue keys in branch names and pull request titles so Linear's GitHub integration can
associate work automatically.

When creating a new OpenSpec proposal, create a corresponding issue in Linear using the
same issue title as the OpenSpec change, and cross-reference the issue in the OpenSpec change.

Prefer branch names like `feature/UT-123-short-description` and PR titles prefixed with `UT-123`.
Pull request descriptions should follow the repository PR template structure:
`Overview`, `Changes`, `Impact`, and `Optional Notes`.

When linking a Linear issue in a pull request description, the Linear issue
reference must use only the bare markdown link format, for example
`[UT-123](https://linear.app/...)`. Do not prefix the Linear issue link with
`Closes`, `Fixes`, `Relates to`, or similar linking phrases unless the user
explicitly requests that wording. When using the repository PR template, place
the bare Linear issue link under `Optional Notes`, not in `Overview`.

Do not use a Linear issue key in created document names; use the OpenSpec change
name instead, where applicable.

Treat GitHub metadata as the automation trigger and Linear issue links as visible resources:

- Create or push branches with the Linear key in the branch name.
- Create PRs with the Linear key in the title and the bare markdown Linear issue link in the `Optional Notes` section of the body.
- Prefer Linear's native GitHub integration attachments for pull requests and branches.
- If the native integration does not attach a pull request or branch and a manual resource is still needed, add it through the Linear MCP issue update `links` field, e.g. `_save_issue(id="UT-123", links=[{"title": "GitHub PR #123", "url": "https://github.com/ORG/REPO/pull/123"}])`.
- Do not add GitHub pull requests or branches as Linear comments.
- Do not rely on manually added Linear resource links to trigger Linear status automation.

## Cross-Repository Wevra/App Changes

While `uniquode.io` consumes Wevra through the temporary workspace checkout, its
CI checks out `Uniquode/wevra` `main` into `wevra/`. For changes that span both
repositories, complete and merge the Wevra side before opening the
`uniquode.io` pull request:

1. Commit, push, and open the Wevra branch/PR.
2. Address Wevra review feedback, then commit and push follow-up changes.
3. Merge the PR to `wevra:main`.
4. Update the local `wevra/` checkout to `main`.
5. Verify the `uniquode.io` changes against the updated Wevra checkout.
6. Commit, push, and open the `uniquode.io` branch/PR.

Do not rely on a `uniquode.io` PR to pass CI against an unmerged Wevra feature
branch unless the workflow is deliberately changed to pin that branch for the PR.

# Stitch

The repository Stitch project is `uniquode.io` with project resource name `projects/5961352154368593199`.
Reuse this project for future design-system, screen-generation, and `DESIGN.md` work unless explicitly
told otherwise.

# Design MCP

The Google Design MCP is available for generic design support such as Google Fonts discovery,
font metadata, Material icon lookup, and Material colour-scheme generation.
Use it for low-level design asset and token decisions; use Stitch for repository-specific
design systems, `DESIGN.md`, and screen work.

# Guide MCP

The Guide MCP is the manager of the development workflow, and will offer important information
and instructions through the development lifecycle, from discussion, planning to implementation and review.

guide:// URIs should be resolved using the Guide MCP's own `read_resource` tool.
Always follow both `instructions` and `additional_agent_instructions` returned by the Guide MCP.
Use `workflow-*` skills directly for common workflow operations with assistance
and support from the Guide MCP.
