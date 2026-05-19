# Agent Notes

Use OpenSpec. Before implementing, identify or create the relevant change and align work with its artifacts.

Use [openspec/adr](openspec/adr) as the source of truth for accepted architecture and platform decisions.

Prefer small, requirement-driven changes. Do not add runtime dependencies or framework structure before a requirement needs them.

Never use `--no-gpg-sign` or `--no-verify` with Git commands.

If `.guide.yaml` exists, treat it as current local project state.
Read `.todo/context.md` at session start when present. Update it at meaningful milestones.

Use `.agents/skills` on demand.
Use `.agents/steering/` on demand; start with `.agents/steering/README.md` when unsure which file applies.
