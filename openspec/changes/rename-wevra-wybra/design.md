## Context

The Wevra package is unpublished, and both the root application workspace and
the nested package checkout are currently clean checkpoints. The rename changes
the project name from Wevra to Wybra across package metadata, Python imports,
CLI entry points, configuration namespaces, module identifiers, documentation,
OpenSpec accepted specs, active OpenSpec planning artefacts, tests, workflows,
and lockfile/source references.

Archived OpenSpec changes are historical records and must remain unchanged.
The `rename-wevra-wybra` OpenSpec change path and change identifier must also
remain unchanged so the transition remains traceable. Content inside this
change may continue to mention both names where it describes the rename.

The root `.bin/` directory contains optional developer shortcut aliases for
package-owned commands. Those shortcuts belong with the renamed Wybra package
and should move into the nested project during implementation.

## Goals / Non-Goals

**Goals:**

- Rename current forward-looking project references from Wevra/wevra/WEVRA to
  Wybra/wybra/WYBRA.
- Rename the Python package namespace, CLI command names, configuration
  namespaces, and module identifiers.
- Update accepted specs under `openspec/specs/**`.
- Update every active OpenSpec change except `rename-wevra-wybra` so future
  planning artefacts describe Wybra.
- Preserve archived OpenSpec changes without edits.
- Move root `.bin/` shortcut aliases into the Wybra project and retarget them to
  `wybra-*` commands.
- Update the renamed package README with concise name-origin context.
- Validate that no unintended Wevra references remain outside explicitly
  excluded historical or transition artefacts.

**Non-Goals:**

- Do not provide compatibility imports, legacy CLI entry points, config
  fallbacks, or migration shims for the old name.
- Do not rewrite archived OpenSpec changes.
- Do not rename the `rename-wevra-wybra` OpenSpec change directory or change ID.
- Do not introduce new runtime dependencies or framework structure.
- Do not change feature behaviour beyond the name and ownership move.

## Decisions

1. Use a script-assisted bulk text rename with hard-coded exclusions.

   Rationale: The rename crosses many text formats and two working trees, so a
   scripted pass is less error-prone than manual edits. The script must exclude
   any `.git` directory at any depth, `openspec/changes/archive/**`, and
   `openspec/changes/rename-wevra-wybra/**`.

   Alternatives considered:
   - Manual edits only: rejected because the change is broad and likely to miss
     references.
   - Shell-only replacement: rejected because exclusions for hidden files,
     nested `.git` directories, and OpenSpec historical paths are easier to make
     explicit and auditable in Python.

2. Treat active OpenSpec changes and accepted specs as forward-looking content.

   Rationale: Active changes and `openspec/specs/**` define current and future
   project vocabulary. They should refer to Wybra after the rename, except for
   the transition change itself.

   Alternatives considered:
   - Leave active changes untouched: rejected because it would keep stale library
     names in work that has not shipped or been archived.
   - Rewrite archives too: rejected because archives are historical records.

3. Move `.bin/` into the nested Wybra project.

   Rationale: The scripts are opt-in developer aliases for package-owned CLI
   commands and currently target `wevra-*`. Keeping them in the root application
   would leave package command conveniences owned by the wrong repository.

   Alternatives considered:
   - Leave `.bin/` at the root: rejected because it couples root tooling to
     package command names.
   - Delete `.bin/`: rejected because the shortcuts are useful developer
     conveniences and can remain optional inside the package repository.

4. Rename without compatibility aliases.

   Rationale: The package is unpublished, and current project guidance is to
   avoid shims unless a concrete compatibility requirement exists.

   Alternatives considered:
   - Keep import aliases and old CLI entry points: rejected because they add
     unnecessary compatibility surface for an unpublished package.

## Risks / Trade-offs

- Bulk rename misses binary, generated, hidden, or unusual files -> Use
  `rg --hidden` audits before and after the script, and inspect remaining
  matches outside excluded paths.
- Bulk rename edits historical records -> Exclude all `.git` directories,
  `openspec/changes/archive/**`, and `openspec/changes/rename-wevra-wybra/**`
  in both discovery and replacement code.
- Filesystem package rename breaks imports or entry points -> Run root and
  package tests, linting, typing, validation, and command smoke checks after the
  rename.
- Repository rename affects remote URLs and GitHub integrations -> Rename the
  GitHub repository deliberately, then verify remotes, workflow references,
  Dependabot, CodeQL, Sourcery, GitGuardian, and source/documentation links.
- Lockfile/source references drift after workspace rename -> Refresh the root
  workspace lock/install state after moving from `wevra` to `wybra`.

## Migration Plan

1. Create a complete current-reference inventory for `wevra`, `Wevra`, and
   `WEVRA` using hidden-file-aware search, excluding `.git` directories,
   `openspec/changes/archive/**`, and
   `openspec/changes/rename-wevra-wybra/**`.
2. Rename filesystem paths and package metadata in the nested package checkout.
3. Move root `.bin/` into the renamed Wybra project and retarget shortcuts to
   `wybra-*`.
4. Run the script-assisted text replacement across eligible tracked files in the
   root workspace and nested package checkout.
5. Update root workspace dependency/source mapping and refresh lock/install
   state.
6. Audit remaining references and manually classify or fix any leftovers.
7. Run OpenSpec validation and the relevant root and package checks.
8. Rename the GitHub repository and verify local remotes and tracked source
   links.

Rollback remains straightforward before commit because both worktrees start from
clean checkpoints. If the rename breaks unexpectedly, restore both repositories
to their pre-rename checkpoint state and re-run with a narrower file set.

## Open Questions

- The exact GitHub repository rename timing should be coordinated with the final
  local branch/PR workflow so remotes and CI targets are consistent.
