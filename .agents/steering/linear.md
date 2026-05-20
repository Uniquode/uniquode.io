# Linear Workflow

Use Linear as the external planning system for this project.

Project:

- Name: `uniquode.io`
- Team: `UTeam`
- Issue identifier prefix: `UT`

Before materialising work as an OpenSpec change, create or identify the Linear issue that represents the work. Record the Linear issue key in the OpenSpec artifacts for traceability.

Workflow:

```text
Linear issue -> OpenSpec change -> implementation -> validation -> commit -> archive -> Linear Done
```

When a Linear issue is completed, archive the corresponding OpenSpec change. When an OpenSpec change is archived, sync any generated main specs before committing.

ADR workflow:

- Keep ADR source files in `openspec/adr/`.
- Keep `openspec/adr/README.md` as the local ADR index.
- Mirror ADR documents into the Linear `uniquode.io` project.
- Keep the Linear `ADR Index` project document in sync with `openspec/adr/README.md`.

Known Linear documents:

- ADR Index: https://linear.app/uniquode/document/adr-index-3f0581fe45f4
- ADR 001: https://linear.app/uniquode/document/adr-001-development-and-implementation-platform-1097723bd2ab
- ADR 002: https://linear.app/uniquode/document/adr-002-runtime-and-deployment-command-conventions-ddb9448a123c

When creating Linear issues from planning:

- Use concise kebab-case titles where they map naturally to OpenSpec change names.
- Include the relevant ADR or Linear document links in the issue description.
- Keep implementation details high-level until the OpenSpec proposal/spec/design captures them.
- Prefer one Linear issue per coherent OpenSpec change.
