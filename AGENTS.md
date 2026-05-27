# Agent Notes

Use OpenSpec. Before implementing, identify or create the relevant change and align work with its artifacts.

Use [openspec/adr](openspec/adr) as the source of truth for accepted architecture and platform decisions.

Prefer small, requirement-driven changes. Do not add runtime dependencies or framework structure before a requirement needs them.

Use UK/AU spelling at all times, including documentation, comments, function names, class names, and variable names.

Never use `--no-gpg-sign` or `--no-verify` with Git commands.

If `.guide.yaml` exists, treat it as current local project state.
Read `.todo/context.md` at session start when present. Update it at meaningful milestones.

Use `.agents/skills` on demand.
Use `.agents/steering/` on demand; start with `.agents/steering/README.md` when unsure which file applies.

# Linear And GitHub

Use Linear issue keys in branch names and pull request titles so Linear can associate GitHub work automatically.
Prefer branch names like `feature/ut-123-short-description` and PR titles prefixed with `UT-123`.
Do not rely on manually added Linear resource links to trigger Linear status automation.

# Stitch

The repository Stitch project is `uniquode.io` with project resource name `projects/5961352154368593199`.
Reuse this project for future design-system, screen-generation, and `DESIGN.md` work unless explicitly told otherwise.

# Design MCP

The Google Design MCP is available for generic design support such as Google Fonts discovery, font metadata, Material icon lookup, and Material colour-scheme generation.
Use it for low-level design asset and token decisions; use Stitch for repository-specific design systems, `DESIGN.md`, and screen work.

# Guide MCP

The Guide MCP is the manager of the development workflow, and will offer important information
and instructions through the development lifecycle, from discussion, planning to implementation and review.

guide:// URIs should be resolved using the Guide MCP's own `read_resource` tool.
Always follow both `instructions` and `additional_agent_instructions` returned by the Guide MCP.
